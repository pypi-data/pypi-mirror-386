# onvif/utils/zeep.py

from lxml.etree import QName
from zeep.xsd.elements.any import Any
from zeep.xsd.utils import max_occurs_iter


class ZeepPatcher:
    """
    Utility class for patching zeep SOAP library to better handle ONVIF xsd:any fields.

    This class provides methods to:
    1. Patch zeep's Any.parse_xmlelements to parse xsd:any fields into structured dicts
    2. Flatten parsed xsd:any fields (_value_1, _value_2, etc.) into parent objects
    3. Parse text values with proper type conversion (bool, int, float, str)

    Usage:
        from onvif.utils.zeep import ZeepPatcher

        # Apply patch at startup
        ZeepPatcher.apply_patch()

        # Check if patched
        if ZeepPatcher.is_patched():
            print("Zeep is patched")

        # Remove patch if needed
        ZeepPatcher.remove_patch()
    """

    # Store original parse_xmlelements before patching
    _original_parse_xmlelements = None
    _is_patched = False

    @staticmethod
    def parse_text_value(value):
        """
        Parse text value with type conversion.

        Converts:
        - "true"/"false" → bool
        - "123" → int
        - "123.45" → float
        - Other → str

        Args:
            value: Text value to parse

        Returns:
            Parsed value with appropriate type
        """
        if value is None:
            return None
        val = value.strip()
        if val.lower() == "true":
            return True
        elif val.lower() == "false":
            return False
        elif val.isdigit():
            return int(val)
        try:
            return float(val)
        except ValueError:
            return val

    @staticmethod
    def _parse_element_recursive(element):
        """
        Recursively parse an XML element and its children into a dictionary.

        Handles:
        - Elements with attributes only (converted to dict)
        - Elements with children only (recursively parsed)
        - Elements with BOTH attributes AND children (merged into single dict)
        - Elements with text content only (type-converted)

        Args:
            element: lxml Element to parse

        Returns:
            Dict, parsed value, or None
        """
        result = {}

        for child in element:
            child_qname = QName(child.tag)
            child_name = child_qname.localname
            child_has_attrib = bool(child.attrib)
            child_has_children = bool(list(child))

            if child_has_attrib and child_has_children:
                # Element has BOTH attributes AND children - merge them
                child_dict = {
                    k: ZeepPatcher.parse_text_value(v) for k, v in child.attrib.items()
                }
                # Recursively parse children and merge into the same dict
                nested = ZeepPatcher._parse_element_recursive(child)
                if nested:
                    child_dict.update(nested)
                result[child_name] = child_dict
            elif child_has_attrib:
                # Element with attributes only
                result[child_name] = {
                    k: ZeepPatcher.parse_text_value(v) for k, v in child.attrib.items()
                }
            elif child_has_children:
                # Element has nested children only
                result[child_name] = ZeepPatcher._parse_element_recursive(child)
            else:
                # Element only has text content
                result[child_name] = ZeepPatcher.parse_text_value(child.text)

        return result if result else None

    @staticmethod
    def _zeep_object_to_dict(obj):
        """
        Convert zeep object to dictionary, including manually added attributes.

        Args:
            obj: Zeep object or primitive value

        Returns:
            Dict or primitive value
        """
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, list):
            return [ZeepPatcher._zeep_object_to_dict(item) for item in obj]
        if isinstance(obj, dict):
            return {k: ZeepPatcher._zeep_object_to_dict(v) for k, v in obj.items()}

        # Handle zeep objects with __values__
        if hasattr(obj, "__values__"):
            result = {}
            for key, val in obj.__values__.items():
                if not key.startswith("_"):  # Skip private fields like _value_1
                    result[key] = ZeepPatcher._zeep_object_to_dict(val)
            return result

        # Handle objects with __dict__
        if hasattr(obj, "__dict__"):
            result = {}
            for key, val in obj.__dict__.items():
                if not key.startswith("_"):
                    result[key] = ZeepPatcher._zeep_object_to_dict(val)
            return result

        return obj

    @staticmethod
    def flatten_xsd_any_fields(obj, _visited=None):
        """
        Post-process zeep objects to flatten xsd:any fields (_value_1, _value_2, etc.) into the main object.

        Zeep uses _value_N fields to store parsed content from xsd:any elements. This function:
        1. Extracts the parsed data from _value_N (which is initially a dict)
        2. Copies values from _value_N to None fields in the main object
        3. Restores _value_N to contain the original XML elements (for zeep compatibility)

        This handles all xsd:any occurrences (_value_1, _value_2, _value_3, etc.), not just the first one.

        Args:
            obj: The zeep object to process
            _visited: Set of visited object IDs to prevent infinite recursion

        Returns:
            The processed object with flattened fields and restored _value_N
        """
        # Track visited objects to prevent infinite recursion
        if _visited is None:
            _visited = set()

        # Handle list of objects
        if isinstance(obj, list):
            for item in obj:
                ZeepPatcher.flatten_xsd_any_fields(item, _visited)
            return obj

        obj_id = id(obj)
        if obj_id in _visited:
            return obj
        _visited.add(obj_id)

        # Skip primitive types
        if isinstance(obj, (dict, str, int, float, bool, type(None))):
            return obj

        if not hasattr(obj, "__dict__"):
            return obj

        # Check if object is a zeep object with __values__
        if hasattr(obj, "__values__"):
            values = obj.__values__

            # Process all _value_N fields (xsd:any can have maxOccurs > 1)
            value_n = 1
            while f"_value_{value_n}" in values:
                value_key = f"_value_{value_n}"
                value_data = values[value_key]

                # Only process if _value_N is a dict (from our patched parser)
                if (
                    isinstance(value_data, dict)
                    and "__original_elements__" in value_data
                ):
                    # Extract original elements first
                    original_elements = value_data.get("__original_elements__")

                    # Check if this is a single-tag wrapper (like {"Capabilities": {...}})
                    # IMPORTANT: We should NOT flatten if the tag name already exists as a field in the schema
                    # This prevents DeviceIO, Recording, etc. from being incorrectly flattened
                    non_private_keys = [
                        k for k in value_data.keys() if not k.startswith("_")
                    ]

                    if len(non_private_keys) == 1:
                        # Single tag wrapper - but check if it should be flattened
                        tag_name = non_private_keys[0]
                        inner_content = value_data[tag_name]

                        # Only flatten if:
                        # 1. The tag_name field exists in schema AND is None (placeholder)
                        # 2. The inner_content is a dict (structured data)
                        # This preserves proper structure for DeviceIO, Recording, etc.
                        should_flatten = (
                            tag_name in values
                            and values[tag_name] is None
                            and isinstance(inner_content, dict)
                        )

                        if should_flatten:
                            # This is truly a wrapper - flatten by copying fields to parent
                            # But still set the tag_name field to the inner_content
                            # Convert zeep object to dict to preserve manually added attributes
                            if hasattr(inner_content, "__values__") or hasattr(
                                inner_content, "__dict__"
                            ):
                                inner_content = ZeepPatcher._zeep_object_to_dict(
                                    inner_content
                                )
                            values[tag_name] = inner_content
                            # Don't copy fields up to parent - keep them in the structured object
                        else:
                            # Not a wrapper - just set the field directly
                            # Convert zeep object to dict to preserve manually added attributes
                            if hasattr(inner_content, "__values__") or hasattr(
                                inner_content, "__dict__"
                            ):
                                inner_content = ZeepPatcher._zeep_object_to_dict(
                                    inner_content
                                )
                            if tag_name in values and values[tag_name] is None:
                                values[tag_name] = inner_content
                            elif tag_name not in values:
                                values[tag_name] = inner_content
                    else:
                        # Multiple tags - copy all non-private fields to their respective locations
                        for key, val in list(value_data.items()):
                            if key.startswith("_"):
                                continue

                            # Convert zeep object to dict to preserve manually added attributes
                            if hasattr(val, "__values__") or hasattr(val, "__dict__"):
                                val = ZeepPatcher._zeep_object_to_dict(val)

                            if key in values and values[key] is None:
                                values[key] = val
                            elif key not in values:
                                values[key] = val

                    # Replace _value_N with ONLY the original elements list
                    if original_elements is not None:
                        values[value_key] = original_elements
                    else:
                        values[value_key] = None

                value_n += 1

        # Also check if object has _value_N attributes in __dict__ (for non-zeep objects)
        else:
            value_n = 1
            while hasattr(obj, f"_value_{value_n}"):
                value_key = f"_value_{value_n}"
                value_data = getattr(obj, value_key)

                if (
                    isinstance(value_data, dict)
                    and "__original_elements__" in value_data
                ):
                    # Extract original elements first (before any modification)
                    original_elements = value_data.get("__original_elements__")

                    # Check if this is a single-tag wrapper
                    non_private_keys = [
                        k for k in value_data.keys() if not k.startswith("_")
                    ]

                    if len(non_private_keys) == 1:
                        # Single tag wrapper - but check if it should be flattened
                        tag_name = non_private_keys[0]
                        inner_content = value_data[tag_name]

                        # Only flatten if the tag_name field exists and is None (placeholder)
                        should_flatten = (
                            hasattr(obj, tag_name)
                            and getattr(obj, tag_name) is None
                            and isinstance(inner_content, dict)
                        )

                        if should_flatten:
                            # Set the field to the structured content
                            # Convert zeep object to dict to preserve manually added attributes
                            if hasattr(inner_content, "__values__") or hasattr(
                                inner_content, "__dict__"
                            ):
                                inner_content = ZeepPatcher._zeep_object_to_dict(
                                    inner_content
                                )
                            setattr(obj, tag_name, inner_content)
                        else:
                            # Not a wrapper - just set the field directly
                            # Convert zeep object to dict to preserve manually added attributes
                            if hasattr(inner_content, "__values__") or hasattr(
                                inner_content, "__dict__"
                            ):
                                inner_content = ZeepPatcher._zeep_object_to_dict(
                                    inner_content
                                )
                            if (
                                hasattr(obj, tag_name)
                                and getattr(obj, tag_name) is None
                            ):
                                setattr(obj, tag_name, inner_content)
                            elif not hasattr(obj, tag_name):
                                setattr(obj, tag_name, inner_content)
                    else:
                        # Multiple tags - copy all non-private fields
                        for key, val in value_data.items():
                            if key.startswith("_"):
                                continue

                            # Convert zeep object to dict to preserve manually added attributes
                            if hasattr(val, "__values__") or hasattr(val, "__dict__"):
                                val = ZeepPatcher._zeep_object_to_dict(val)

                            if hasattr(obj, key) and getattr(obj, key) is None:
                                setattr(obj, key, val)
                            elif not hasattr(obj, key):
                                setattr(obj, key, val)

                    # Replace _value_N with ONLY the original elements list
                    if original_elements is not None:
                        setattr(obj, value_key, original_elements)
                    else:
                        setattr(obj, value_key, None)

                value_n += 1

        # Recursively process nested objects
        if hasattr(obj, "__values__"):
            for val in obj.__values__.values():
                if val is not None and not isinstance(
                    val, (dict, str, int, float, bool)
                ):
                    if hasattr(val, "__dict__"):
                        ZeepPatcher.flatten_xsd_any_fields(val, _visited)
                    elif isinstance(val, list):
                        for item in val:
                            if hasattr(item, "__dict__"):
                                ZeepPatcher.flatten_xsd_any_fields(item, _visited)
        else:
            for key, val in list(obj.__dict__.items()):
                if val is not None and not isinstance(
                    val, (dict, str, int, float, bool)
                ):
                    if hasattr(val, "__dict__"):
                        ZeepPatcher.flatten_xsd_any_fields(val, _visited)
                    elif isinstance(val, list):
                        for item in val:
                            if hasattr(item, "__dict__"):
                                ZeepPatcher.flatten_xsd_any_fields(item, _visited)

        return obj

    @staticmethod
    def _patched_parse_xmlelements(self, xmlelements, schema, name=None, context=None):
        """
        Patched version of zeep's Any.parse_xmlelements method.

        This method parses xsd:any fields into structured dictionaries instead of
        leaving them as raw XML elements, making them easier to work with.

        Args:
            self: The Any instance (injected by zeep)
            xmlelements: Deque of XML elements to parse
            schema: Zeep schema object
            name: Optional element name
            context: Optional parsing context

        Returns:
            Dict containing parsed data with '__original_elements__' key for restoration
        """
        parsed_result = {}
        original_elements = []  # Store original XML elements

        for _ in max_occurs_iter(self.max_occurs):
            if not xmlelements:
                break
            xmlelement = xmlelements.popleft()

            # Store original element before processing
            original_elements.append(xmlelement)

            tag_name = QName(xmlelement.tag).localname
            children = list(xmlelement)

            if children and schema:
                child_result = {}

                # If xmlelement itself has attributes, add them first
                if xmlelement.attrib:
                    child_result.update(
                        {
                            k: ZeepPatcher.parse_text_value(v)
                            for k, v in xmlelement.attrib.items()
                        }
                    )

                for child in children:
                    child_qname = QName(child.tag)
                    child_localname = child_qname.localname

                    # If child has attributes, parse manually to preserve them
                    # Schema parsing often loses attributes not in schema definition
                    if child.attrib:
                        parsed = {}
                        # Add attributes first
                        parsed.update(
                            {
                                k: ZeepPatcher.parse_text_value(v)
                                for k, v in child.attrib.items()
                            }
                        )
                        # Then add nested children
                        nested = ZeepPatcher._parse_element_recursive(child)
                        if nested:
                            parsed.update(nested)
                        child_result[child_localname] = parsed
                        continue

                    # No attributes - try schema parsing first
                    try:
                        xsd_el = schema.get_element(child_qname)
                        val = xsd_el.parse_xmlelement(
                            child, schema=schema, allow_none=True, context=context
                        )
                        child_result[child_qname.localname] = val
                    except Exception:
                        # If schema lookup fails, try to parse manually
                        parsed = {}

                        # Parse child's own attributes first (if any)
                        if child.attrib:
                            parsed.update(
                                {
                                    k: ZeepPatcher.parse_text_value(v)
                                    for k, v in child.attrib.items()
                                }
                            )

                        # Parse child's nested children (if any)
                        nested = ZeepPatcher._parse_element_recursive(child)
                        if nested:
                            parsed.update(nested)

                        # If no attributes and no children, try text content
                        if not parsed:
                            parsed = ZeepPatcher.parse_text_value(child.text)

                        child_result[child_qname.localname] = parsed

                parsed_result[tag_name] = child_result
            else:
                parsed_result[tag_name] = ZeepPatcher.parse_text_value(xmlelement.text)

        # Store original elements in a special key for later restoration
        if original_elements:
            parsed_result["__original_elements__"] = original_elements

        return parsed_result

    @classmethod
    def apply_patch(cls):
        """
        Inject the custom parse_xmlelements method into zeep.xsd.elements.any.Any.

        This enables better parsing of xsd:any fields in ONVIF SOAP responses.
        Should be called once at application startup.

        Example:
            from onvif.utils.zeep import ZeepPatcher
            ZeepPatcher.apply_patch()
        """
        if not cls._is_patched:
            cls._original_parse_xmlelements = Any.parse_xmlelements
            Any.parse_xmlelements = cls._patched_parse_xmlelements
            cls._is_patched = True

    @classmethod
    def remove_patch(cls):
        """
        Restore the original parse_xmlelements method.

        Reverts zeep to its original behavior. Useful for testing or debugging.

        Example:
            from onvif.utils.zeep import ZeepPatcher
            ZeepPatcher.remove_patch()
        """
        if cls._is_patched and cls._original_parse_xmlelements is not None:
            Any.parse_xmlelements = cls._original_parse_xmlelements
            cls._is_patched = False

    @classmethod
    def is_patched(cls):
        """
        Check if the patch is currently applied.

        Returns:
            bool: True if patch is active, False otherwise

        Example:
            from onvif.utils.zeep import ZeepPatcher
            if ZeepPatcher.is_patched():
                print("Zeep patch is active")
        """
        return cls._is_patched
