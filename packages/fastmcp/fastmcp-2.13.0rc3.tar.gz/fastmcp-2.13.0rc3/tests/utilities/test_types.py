import base64
import os
import tempfile
from pathlib import Path
from types import EllipsisType
from typing import Annotated, Any

import pytest
from mcp.types import BlobResourceContents, TextResourceContents
from pydantic import Field

from fastmcp.utilities.types import (
    Audio,
    File,
    Image,
    find_kwarg_by_type,
    get_cached_typeadapter,
    is_class_member_of_type,
    issubclass_safe,
    replace_type,
)


class BaseClass:
    pass


class ChildClass(BaseClass):
    pass


class OtherClass:
    pass


class TestIsClassMemberOfType:
    def test_basic_subclass_check(self):
        """Test that a subclass is recognized as a member of the base class."""
        assert is_class_member_of_type(ChildClass, BaseClass)

    def test_self_is_member(self):
        """Test that a class is a member of itself."""
        assert is_class_member_of_type(BaseClass, BaseClass)

    def test_unrelated_class_is_not_member(self):
        """Test that an unrelated class is not a member of the base class."""
        assert not is_class_member_of_type(OtherClass, BaseClass)

    def test_typing_union_with_member_is_member(self):
        """Test that Union type with a member class is detected as a member."""
        union_type1: Any = ChildClass | OtherClass
        union_type2: Any = OtherClass | ChildClass

        assert is_class_member_of_type(union_type1, BaseClass)
        assert is_class_member_of_type(union_type2, BaseClass)

    def test_typing_union_without_member_is_not_member(self):
        """Test that Union type without any member class is not a member."""
        union_type: Any = OtherClass | str
        assert not is_class_member_of_type(union_type, BaseClass)

    def test_pipe_union_with_member_is_member(self):
        """Test that pipe syntax union with a member class is detected as a member."""
        union_pipe1: Any = ChildClass | OtherClass
        union_pipe2: Any = OtherClass | ChildClass

        assert is_class_member_of_type(union_pipe1, BaseClass)
        assert is_class_member_of_type(union_pipe2, BaseClass)

    def test_pipe_union_without_member_is_not_member(self):
        """Test that pipe syntax union without any member class is not a member."""
        union_pipe: Any = OtherClass | str
        assert not is_class_member_of_type(union_pipe, BaseClass)

    def test_annotated_member_is_member(self):
        """Test that Annotated with a member class is detected as a member."""
        annotated1: Any = Annotated[ChildClass, "metadata"]
        annotated2: Any = Annotated[BaseClass, "metadata"]

        assert is_class_member_of_type(annotated1, BaseClass)
        assert is_class_member_of_type(annotated2, BaseClass)

    def test_annotated_non_member_is_not_member(self):
        """Test that Annotated with a non-member class is not a member."""
        annotated: Any = Annotated[OtherClass, "metadata"]
        assert not is_class_member_of_type(annotated, BaseClass)

    def test_annotated_with_union_member_is_member(self):
        """Test that Annotated with a Union containing a member class is a member."""
        # Test with both Union styles
        annotated1: Any = Annotated[ChildClass | OtherClass, "metadata"]
        annotated2: Any = Annotated[ChildClass | OtherClass, "metadata"]

        assert is_class_member_of_type(annotated1, BaseClass)
        assert is_class_member_of_type(annotated2, BaseClass)

    def test_nested_annotated_with_member_is_member(self):
        """Test that nested Annotated with a member class is a member."""
        annotated: Any = Annotated[Annotated[ChildClass, "inner"], "outer"]
        assert is_class_member_of_type(annotated, BaseClass)

    def test_none_is_not_member(self):
        """Test that None is not a member of any class."""
        assert not is_class_member_of_type(None, BaseClass)  # type: ignore

    def test_generic_type_is_not_member(self):
        """Test that generic types are not members based on their parameter types."""
        list_type: Any = list[ChildClass]
        assert not is_class_member_of_type(list_type, BaseClass)


class TestIsSubclassSafe:
    def test_child_is_subclass_of_parent(self):
        """Test that a child class is recognized as a subclass of its parent."""
        assert issubclass_safe(ChildClass, BaseClass)

    def test_class_is_subclass_of_itself(self):
        """Test that a class is a subclass of itself."""
        assert issubclass_safe(BaseClass, BaseClass)

    def test_unrelated_class_is_not_subclass(self):
        """Test that an unrelated class is not a subclass."""
        assert not issubclass_safe(OtherClass, BaseClass)

    def test_none_type_handled_safely(self):
        """Test that None type is handled safely without raising TypeError."""
        assert not issubclass_safe(None, BaseClass)  # type: ignore


class TestImage:
    def test_image_initialization_with_path(self):
        """Test image initialization with a path."""
        # Mock test - we're not actually going to read a file
        image = Image(path="test.png")
        assert image.path is not None
        assert image.data is None
        assert image._mime_type == "image/png"

    def test_image_path_expansion_with_tilde(self):
        """Test that ~ is expanded to the user's home directory."""
        image = Image(path="~/test.png")
        assert image.path is not None
        assert not str(image.path).startswith("~")
        assert str(image.path).startswith(os.path.expanduser("~"))

    def test_image_path_expansion_with_env_var(self, monkeypatch):
        """Test that environment variables are expanded."""
        test_dir = tempfile.mkdtemp()
        monkeypatch.setenv("TEST_PATH", test_dir)
        image = Image(path="$TEST_PATH/test.png")
        assert image.path is not None
        assert not str(image.path).startswith("$TEST_PATH")
        expected_path = Path(test_dir) / "test.png"
        assert image.path == expected_path

    def test_image_initialization_with_data(self):
        """Test image initialization with data."""
        image = Image(data=b"test")
        assert image.path is None
        assert image.data == b"test"
        assert image._mime_type == "image/png"  # Default for raw data

    def test_image_initialization_with_format(self):
        """Test image initialization with a specific format."""
        image = Image(data=b"test", format="jpeg")
        assert image._mime_type == "image/jpeg"

    def test_missing_data_and_path_raises_error(self):
        """Test that error is raised when neither path nor data is provided."""
        with pytest.raises(ValueError, match="Either path or data must be provided"):
            Image()

    def test_both_data_and_path_raises_error(self):
        """Test that error is raised when both path and data are provided."""
        with pytest.raises(
            ValueError, match="Only one of path or data can be provided"
        ):
            Image(path="test.png", data=b"test")

    def test_get_mime_type_from_path(self, tmp_path):
        """Test MIME type detection from file extension."""
        extensions = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".unknown": "application/octet-stream",
        }

        for ext, mime in extensions.items():
            path = tmp_path / f"test{ext}"
            path.write_bytes(b"fake image data")
            img = Image(path=path)
            assert img._mime_type == mime

    def test_to_image_content(self, tmp_path, monkeypatch):
        """Test conversion to ImageContent."""
        # Test with path
        img_path = tmp_path / "test.png"
        test_data = b"fake image data"
        img_path.write_bytes(test_data)

        img = Image(path=img_path)
        content = img.to_image_content()

        assert content.type == "image"
        assert content.mimeType == "image/png"
        assert content.data == base64.b64encode(test_data).decode()

        # Test with data
        img = Image(data=test_data, format="jpeg")
        content = img.to_image_content()

        assert content.type == "image"
        assert content.mimeType == "image/jpeg"
        assert content.data == base64.b64encode(test_data).decode()

    def test_to_image_content_error(self, monkeypatch):
        """Test error case in to_image_content."""
        # Create an Image with neither path nor data (shouldn't happen due to __init__ checks,
        # but testing the method's own error handling)
        img = Image(data=b"test")
        monkeypatch.setattr(img, "path", None)
        monkeypatch.setattr(img, "data", None)

        with pytest.raises(ValueError, match="No image data available"):
            img.to_image_content()


class TestAudio:
    def test_audio_initialization_with_path(self):
        """Test audio initialization with a path."""
        # Mock test - we're not actually going to read a file
        audio = Audio(path="test.wav")
        assert audio.path is not None
        assert audio.data is None
        assert audio._mime_type == "audio/wav"

    def test_audio_path_expansion_with_tilde(self):
        """Test that ~ is expanded to the user's home directory."""
        audio = Audio(path="~/test.wav")
        assert audio.path is not None
        assert not str(audio.path).startswith("~")
        assert str(audio.path).startswith(os.path.expanduser("~"))

    def test_audio_path_expansion_with_env_var(self, monkeypatch):
        """Test that environment variables are expanded."""
        test_dir = tempfile.mkdtemp()
        monkeypatch.setenv("TEST_AUDIO_PATH", test_dir)
        audio = Audio(path="$TEST_AUDIO_PATH/test.wav")
        assert audio.path is not None
        assert not str(audio.path).startswith("$TEST_AUDIO_PATH")
        expected_path = Path(test_dir) / "test.wav"
        assert audio.path == expected_path

    def test_audio_initialization_with_data(self):
        """Test audio initialization with data."""
        audio = Audio(data=b"test")
        assert audio.path is None
        assert audio.data == b"test"
        assert audio._mime_type == "audio/wav"  # Default for raw data

    def test_audio_initialization_with_format(self):
        """Test audio initialization with a specific format."""
        audio = Audio(data=b"test", format="mp3")
        assert audio._mime_type == "audio/mp3"

    def test_missing_data_and_path_raises_error(self):
        """Test that error is raised when neither path nor data is provided."""
        with pytest.raises(ValueError, match="Either path or data must be provided"):
            Audio()

    def test_both_data_and_path_raises_error(self):
        """Test that error is raised when both path and data are provided."""
        with pytest.raises(
            ValueError, match="Only one of path or data can be provided"
        ):
            Audio(path="test.wav", data=b"test")

    def test_get_mime_type_from_path(self, tmp_path):
        """Test MIME type detection from file extension."""
        extensions = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
            ".unknown": "application/octet-stream",
        }

        for ext, mime in extensions.items():
            path = tmp_path / f"test{ext}"
            path.write_bytes(b"fake audio data")
            audio = Audio(path=path)
            assert audio._mime_type == mime

    def test_to_audio_content(self, tmp_path, monkeypatch):
        """Test conversion to AudioContent."""
        # Test with path
        audio_path = tmp_path / "test.wav"
        test_data = b"fake audio data"
        audio_path.write_bytes(test_data)

        audio = Audio(path=audio_path)
        content = audio.to_audio_content()

        assert content.type == "audio"
        assert content.mimeType == "audio/wav"
        assert content.data == base64.b64encode(test_data).decode()

        # Test with data
        audio = Audio(data=test_data, format="mp3")
        content = audio.to_audio_content()

        assert content.type == "audio"
        assert content.mimeType == "audio/mp3"
        assert content.data == base64.b64encode(test_data).decode()

    def test_to_audio_content_error(self, monkeypatch):
        """Test error case in to_audio_content."""
        # Create an Audio with neither path nor data (shouldn't happen due to __init__ checks,
        # but testing the method's own error handling)
        audio = Audio(data=b"test")
        monkeypatch.setattr(audio, "path", None)
        monkeypatch.setattr(audio, "data", None)

        with pytest.raises(ValueError, match="No audio data available"):
            audio.to_audio_content()

    def test_to_audio_content_with_override_mime_type(self, tmp_path):
        """Test conversion to AudioContent with override MIME type."""
        audio_path = tmp_path / "test.wav"
        test_data = b"fake audio data"
        audio_path.write_bytes(test_data)

        audio = Audio(path=audio_path)
        content = audio.to_audio_content(mime_type="audio/custom")

        assert content.type == "audio"
        assert content.mimeType == "audio/custom"
        assert content.data == base64.b64encode(test_data).decode()


class TestFile:
    def test_file_initialization_with_path(self):
        """Test file initialization with a path."""
        # Mock test - we're not actually going to read a file
        file = File(path="test.txt")
        assert file.path is not None
        assert file.data is None
        assert file._mime_type == "text/plain"

    def test_file_path_expansion_with_tilde(self):
        """Test that ~ is expanded to the user's home directory."""
        file = File(path="~/test.txt")
        assert file.path is not None
        assert not str(file.path).startswith("~")
        assert str(file.path).startswith(os.path.expanduser("~"))

    def test_file_path_expansion_with_env_var(self, monkeypatch):
        """Test that environment variables are expanded."""
        test_dir = tempfile.mkdtemp()
        monkeypatch.setenv("TEST_FILE_PATH", test_dir)
        file = File(path="$TEST_FILE_PATH/test.txt")
        assert file.path is not None
        assert not str(file.path).startswith("$TEST_FILE_PATH")
        expected_path = Path(test_dir) / "test.txt"
        assert file.path == expected_path

    def test_file_initialization_with_data(self):
        """Test initialization with data and format."""
        test_data = b"test data"
        file = File(data=test_data, format="octet-stream")
        assert file.data == test_data
        # The format parameter should set the MIME type
        assert file._mime_type == "application/octet-stream"
        assert file._name is None
        assert file.annotations is None

    def test_file_initialization_with_format(self):
        """Test file initialization with a specific format."""
        file = File(data=b"test", format="pdf")
        assert file._mime_type == "application/pdf"

    def test_file_initialization_with_name(self):
        """Test file initialization with a custom name."""
        file = File(data=b"test", name="custom")
        assert file._name == "custom"

    def test_missing_data_and_path_raises_error(self):
        """Test that error is raised when neither path nor data is provided."""
        with pytest.raises(ValueError, match="Either path or data must be provided"):
            File()

    def test_both_data_and_path_raises_error(self):
        """Test that error is raised when both path and data are provided."""
        with pytest.raises(
            ValueError, match="Only one of path or data can be provided"
        ):
            File(path="test.txt", data=b"test")

    def test_get_mime_type_from_path(self, tmp_path):
        """Test MIME type detection from file extension."""
        file_path = tmp_path / "test.txt"
        file_path.write_text(
            "test content"
        )  # Need to write content for MIME type detection
        file = File(path=file_path)
        # The MIME type should be detected from the .txt extension
        assert file._mime_type == "text/plain"

    def test_to_resource_content_with_path(self, tmp_path):
        """Test conversion to ResourceContent with path."""
        file_path = tmp_path / "test.txt"
        test_data = b"test file data"
        file_path.write_bytes(test_data)

        file = File(path=file_path)
        resource = file.to_resource_content()

        assert resource.type == "resource"
        assert resource.resource.mimeType == "text/plain"
        # Convert both to strings for comparison
        assert str(resource.resource.uri) == file_path.resolve().as_uri()
        if isinstance(resource.resource, BlobResourceContents):
            assert resource.resource.blob == base64.b64encode(test_data).decode()

    def test_to_resource_content_with_data(self):
        """Test conversion to ResourceContent with data."""
        test_data = b"test file data"
        file = File(data=test_data, format="pdf")
        resource = file.to_resource_content()

        assert resource.type == "resource"
        assert resource.resource.mimeType == "application/pdf"
        # Convert URI to string for comparison
        assert str(resource.resource.uri) == "file:///resource.pdf"
        if isinstance(resource.resource, BlobResourceContents):
            assert resource.resource.blob == base64.b64encode(test_data).decode()

    def test_to_resource_content_with_text_data(self):
        """Test conversion to ResourceContent with text data (TextResourceContents)."""
        test_data = b"hello world"
        file = File(data=test_data, format="plain")
        resource = file.to_resource_content()
        assert resource.type == "resource"
        # Should be TextResourceContents for text/plain
        assert isinstance(resource.resource, TextResourceContents)
        assert resource.resource.mimeType == "text/plain"
        assert resource.resource.text == "hello world"

    def test_to_resource_content_error(self, monkeypatch):
        """Test error case in to_resource_content."""
        file = File(data=b"test")
        monkeypatch.setattr(file, "path", None)
        monkeypatch.setattr(file, "data", None)

        with pytest.raises(ValueError, match="No resource data available"):
            file.to_resource_content()

    def test_to_resource_content_with_override_mime_type(self, tmp_path):
        """Test conversion to ResourceContent with override MIME type."""
        file_path = tmp_path / "test.txt"
        test_data = b"test file data"
        file_path.write_bytes(test_data)

        file = File(path=file_path)
        resource = file.to_resource_content(mime_type="application/custom")

        assert resource.resource.mimeType == "application/custom"


class TestFindKwargByType:
    def test_exact_type_match(self):
        """Test finding parameter with exact type match."""

        def func(a: int, b: str, c: BaseClass):
            pass

        assert find_kwarg_by_type(func, BaseClass) == "c"

    def test_no_matching_parameter(self):
        """Test finding parameter when no match exists."""

        def func(a: int, b: str, c: OtherClass):
            pass

        assert find_kwarg_by_type(func, BaseClass) is None

    def test_parameter_with_no_annotation(self):
        """Test with a parameter that has no type annotation."""

        def func(a: int, b, c: BaseClass):
            pass

        assert find_kwarg_by_type(func, BaseClass) == "c"

    def test_union_type_match_pipe_syntax(self):
        """Test finding parameter with union type using pipe syntax."""

        def func(a: int, b: str | BaseClass, c: str):
            pass

        assert find_kwarg_by_type(func, BaseClass) == "b"

    def test_union_type_match_typing_union(self):
        """Test finding parameter with union type using Union."""

        def func(a: int, b: str | BaseClass, c: str):
            pass

        assert find_kwarg_by_type(func, BaseClass) == "b"

    def test_annotated_type_match(self):
        """Test finding parameter with Annotated type."""

        def func(a: int, b: Annotated[BaseClass, "metadata"], c: str):
            pass

        assert find_kwarg_by_type(func, BaseClass) == "b"

    def test_method_parameter(self):
        """Test finding parameter in a class method."""

        class TestClass:
            def method(self, a: int, b: BaseClass):
                pass

        instance = TestClass()
        assert find_kwarg_by_type(instance.method, BaseClass) == "b"

    def test_static_method_parameter(self):
        """Test finding parameter in a static method."""

        class TestClass:
            @staticmethod
            def static_method(a: int, b: BaseClass, c: str):
                pass

        assert find_kwarg_by_type(TestClass.static_method, BaseClass) == "b"

    def test_class_method_parameter(self):
        """Test finding parameter in a class method."""

        class TestClass:
            @classmethod
            def class_method(cls, a: int, b: BaseClass, c: str):
                pass

        assert find_kwarg_by_type(TestClass.class_method, BaseClass) == "b"

    def test_multiple_matching_parameters(self):
        """Test finding first parameter when multiple matches exist."""

        def func(a: BaseClass, b: str, c: BaseClass):
            pass

        # Should return the first match
        assert find_kwarg_by_type(func, BaseClass) == "a"

    def test_subclass_match(self):
        """Test finding parameter with a subclass of the target type."""

        def func(a: int, b: ChildClass, c: str):
            pass

        assert find_kwarg_by_type(func, BaseClass) == "b"

    def test_nonstandard_annotation(self):
        """Test finding parameter with a nonstandard annotation like an
        instance. This is irregular."""

        SENTINEL = object()

        def func(a: int, b: SENTINEL, c: str):  # type: ignore
            pass

        assert find_kwarg_by_type(func, SENTINEL) is None  # type: ignore

    def test_ellipsis_annotation(self):
        """Test finding parameter with an ellipsis annotation."""

        def func(a: int, b: EllipsisType, c: str):  # type: ignore  # noqa: F821
            pass

        assert find_kwarg_by_type(func, EllipsisType) == "b"  # type: ignore

    def test_missing_type_annotation(self):
        """Test finding parameter with a missing type annotation."""

        def func(a: int, b, c: str):
            pass

        assert find_kwarg_by_type(func, str) == "c"


class TestReplaceType:
    @pytest.mark.parametrize(
        "input,type_map,expected",
        [
            (int, {}, int),
            (int, {int: str}, str),
            (int, {int: int}, int),
            (int, {int: float, bool: str}, float),
            (bool, {int: float, bool: str}, str),
            (int, {int: list[int]}, list[int]),
            (list[int], {int: str}, list[str]),
            (list[int], {int: list[str]}, list[list[str]]),
            (
                list[int],
                {int: float, list[int]: bool},
                bool,
            ),  # list[int] will match before int
            (list[int | bool], {int: str}, list[str | bool]),
            (list[list[int]], {int: str}, list[list[str]]),
        ],
    )
    def test_replace_type(self, input, type_map, expected):
        """Test replacing a type with another type."""
        assert replace_type(input, type_map) == expected


class TestAnnotationStringDescriptions:
    """Test the new functionality for string descriptions in Annotated types."""

    def test_get_cached_typeadapter_with_string_descriptions(self):
        """Test TypeAdapter creation with string descriptions."""

        def func(name: Annotated[str, "The user's name"]) -> str:
            return f"Hello {name}"

        adapter = get_cached_typeadapter(func)
        schema = adapter.json_schema()

        # Should have description in schema
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert schema["properties"]["name"]["description"] == "The user's name"

    def test_multiple_string_annotations(self):
        """Test function with multiple string-annotated parameters."""

        def func(
            name: Annotated[str, "User's name"],
            email: Annotated[str, "User's email"],
            age: int,
        ) -> str:
            return f"{name} ({email}) is {age}"

        adapter = get_cached_typeadapter(func)
        schema = adapter.json_schema()

        # Both annotated parameters should have descriptions
        assert schema["properties"]["name"]["description"] == "User's name"
        assert schema["properties"]["email"]["description"] == "User's email"
        # Non-annotated parameter should not have description
        assert "description" not in schema["properties"]["age"]

    def test_annotated_with_more_than_string_unchanged(self):
        """Test that Annotated with more than just a string is unchanged."""

        def func(name: Annotated[str, "desc", "extra"]) -> str:
            return f"Hello {name}"

        adapter = get_cached_typeadapter(func)
        schema = adapter.json_schema()

        # Should not have description since it's not exactly length 2
        assert "description" not in schema["properties"]["name"]

    def test_annotated_with_non_string_unchanged(self):
        """Test that Annotated with non-string second arg is unchanged."""

        def func(name: Annotated[str, 42]) -> str:
            return f"Hello {name}"

        adapter = get_cached_typeadapter(func)
        schema = adapter.json_schema()

        # Should not have description since second arg is not string
        assert "description" not in schema["properties"]["name"]

    def test_existing_field_unchanged(self):
        """Test that existing Field annotations are unchanged."""

        def func(name: Annotated[str, Field(description="Field desc")]) -> str:
            return f"Hello {name}"

        adapter = get_cached_typeadapter(func)
        schema = adapter.json_schema()

        # Should keep the Field description
        assert schema["properties"]["name"]["description"] == "Field desc"
