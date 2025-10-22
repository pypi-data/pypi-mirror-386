from collections import defaultdict
from collections.abc import Iterable, Sequence
from logging import getLogger

import google.protobuf.descriptor_pb2 as pb

import nebius.base.protos.pythonic_names as names
from nebius.api.nebius import (
    EnumPySDKSettings,
    EnumValuePySDKSettings,
    FieldPySDKSettings,
    MessagePySDKSettings,
    MethodPySDKSettings,
    OneofPySDKSettings,
    ServicePySDKSettings,
    enum_py_sdk,
    enum_value_py_sdk,
    field_py_sdk,
    message_py_sdk,
    method_py_sdk,
    oneof_py_sdk,
    service_py_sdk,
)
from nebius.base.protos.compiler.pygen import ImportedSymbol, ImportPath

log = getLogger(__name__)


class DescriptorError(Exception):
    pass


class FieldNotMessageError(DescriptorError):
    def __init__(self, field: "Field") -> None:
        super().__init__(
            f"Field {field.name} of {field.containing_message.full_type_name} is not "
            "a message type."
        )


class FieldNotEnumError(DescriptorError):
    def __init__(self, field: "Field") -> None:
        super().__init__(
            f"Field {field.name} of {field.containing_message.full_type_name} is not "
            "a enum type."
        )


class SourceInfo:
    def __init__(self, info: pb.SourceCodeInfo.Location | None = None) -> None:
        if info is not None:
            self._info = info
        else:
            self._info = pb.SourceCodeInfo.Location(
                leading_comments="",
                trailing_comments="",
                leading_detached_comments=[],
                span=[-1, -1, -1],
            )

    @property
    def leading_detached_comments(self) -> Sequence[str]:
        return self._info.leading_detached_comments

    @property
    def leading_comments(self) -> str:
        return self._info.leading_comments

    @property
    def trailing_comments(self) -> str:
        return self._info.trailing_comments

    @property
    def start_line(self) -> int:
        return self._info.span[0]

    @property
    def start_column(self) -> int:
        return self._info.span[1]

    @property
    def end_line(self) -> int:
        if len(self._info.span) > 3:
            return self._info.span[2]
        return self._info.span[0]

    @property
    def end_column(self) -> int:
        return self._info.span[-1]


class Descriptor:
    @property
    def name(self) -> str:
        return self.descriptor.name  # type: ignore

    @property
    def pythonic_name(self) -> str:
        raise NotImplementedError("Subclasses must implement pythonic_name property")


class DescriptorNameError(DescriptorError):
    def __init__(self, descriptor: Descriptor, error: Exception) -> None:
        super().__init__(f"{descriptor!r} has error with name: {error}")


class DuplicatesError(DescriptorError):
    def __init__(
        self,
        descriptor: Descriptor,
        duplicates: Iterable[list[Descriptor]],
        inner_errors: list["DuplicatesError"] | None = None,
    ) -> None:
        lines = "\n".join(
            f"{group[0].pythonic_name}: {group!r}" for group in duplicates
        )
        if lines != "":
            lines = f"{descriptor!r} has duplicate names for children:\n{lines}"
        if inner_errors is not None and len(inner_errors) > 0:
            if len(lines) != 0:
                lines += "\n"
            lines += "\n".join(str(e) for e in inner_errors)

        super().__init__(lines)


class EnumValue(Descriptor):
    def __init__(
        self,
        descriptor: pb.EnumValueDescriptorProto,
        containing_enum: "Enum",
        index: int = -1,
    ) -> None:
        self.descriptor = descriptor
        self.containing_enum = containing_enum
        self._pythonic_name = ""
        self._index = index
        self._path_in_file: Sequence[int] | None = None
        self._settings = EnumValuePySDKSettings(
            descriptor.options.Extensions[enum_value_py_sdk]  # type: ignore
        )

    @property
    def source_info(self) -> SourceInfo:
        if self.path_in_file in self.containing_enum.containing_file.source_code_info:
            return SourceInfo(
                self.containing_enum.containing_file.source_code_info[self.path_in_file]
            )
        return SourceInfo()

    @property
    def path_in_file(self) -> Sequence[int]:
        if self._path_in_file is None:
            self._path_in_file = tuple(
                tuple(self.containing_enum.path_in_file)
                + tuple(
                    [
                        pb.EnumDescriptorProto.VALUE_FIELD_NUMBER,
                        self._index,
                    ]
                )
            )
        return self._path_in_file

    @property
    def pythonic_name(self) -> str:
        if self._pythonic_name == "":
            try:
                self._pythonic_name = names.enum_value(
                    self.name,
                    self.containing_enum.name,
                    self._settings.name,
                    self.containing_enum.full_type_name + "." + self.name,
                )
            except names.NameError as e:
                raise DescriptorNameError(self, e) from None
        return self._pythonic_name

    @property
    def number(self) -> int:
        return self.descriptor.number  # type:ignore[no-any-return,unused-ignore]

    @property
    def pb2(self) -> ImportedSymbol:
        c_import = self.containing_enum.pb2
        return ImportedSymbol(c_import.name + "." + self.name, c_import.import_path)

    def __repr__(self) -> str:
        return f"EnumValue({self.containing_enum.full_type_name}.{self.name})"


class Enum(Descriptor):
    def __init__(
        self,
        descriptor: pb.EnumDescriptorProto,
        containing_file: "File",
        containing_message: "Message|None" = None,
        index: int = -1,
    ) -> None:
        self.descriptor = descriptor
        self.containing_message = containing_message
        self.containing_file = containing_file
        self._values: list[EnumValue] | None = None
        self._values_dict: dict[str, EnumValue] | None = None
        self._pythonic_name = ""
        self._index = index
        self._path_in_file: Sequence[int] | None = None
        self._settings = EnumPySDKSettings(
            descriptor.options.Extensions[enum_py_sdk]  # type: ignore
        )
        self._checked = False

    def check_names(self) -> None:
        if self._checked:
            return
        val_names = defaultdict[str, list[Descriptor]](list[Descriptor])
        for val in self.values:
            val_names[val.pythonic_name].append(val)

        duplicates: list[list[Descriptor]] = [
            group for group in val_names.values() if len(group) > 1
        ]
        if duplicates:
            raise DuplicatesError(self, duplicates)
        self._checked = True

    @property
    def source_info(self) -> SourceInfo:
        if self.path_in_file in self.containing_file.source_code_info:
            return SourceInfo(self.containing_file.source_code_info[self.path_in_file])
        return SourceInfo()

    @property
    def path_in_file(self) -> Sequence[int]:
        if self._path_in_file is None:
            if self.containing_message is not None:
                self._path_in_file = tuple(
                    tuple(self.containing_message.path_in_file)
                    + tuple(
                        [
                            pb.DescriptorProto.ENUM_TYPE_FIELD_NUMBER,
                            self._index,
                        ]
                    )
                )
            else:
                self._path_in_file = tuple(
                    [
                        pb.FileDescriptorProto.ENUM_TYPE_FIELD_NUMBER,
                        self._index,
                    ]
                )
        return self._path_in_file

    def __repr__(self) -> str:
        return f"Enum({self.full_type_name})"

    @property
    def pythonic_name(self) -> str:
        if self._pythonic_name == "":
            try:
                self._pythonic_name = names.enum(
                    self.full_type_name,
                    self._settings.name,
                )
            except names.NameError as e:
                raise DescriptorNameError(self, e) from None
        return self._pythonic_name

    @property
    def values(self) -> list[EnumValue]:
        if self._values is None:
            self._values = [
                EnumValue(val, self, index=i)
                for i, val in enumerate(self.descriptor.value)
            ]
        return self._values

    @property
    def values_dict(self) -> dict[str, EnumValue]:
        if self._values_dict is None:
            self._values_dict = {val.name: val for val in self.values}
        return self._values_dict

    @property
    def no_wrap(self) -> bool:
        if self.containing_file.skipped:
            return True
        return False

    @property
    def full_type_name(self) -> str:
        if self.containing_message is not None:
            return self.containing_message.full_type_name + "." + self.name
        return "." + self.containing_file.package + "." + self.name

    @property
    def export_path(self) -> ImportedSymbol:
        if self.containing_message is not None:
            c_import = self.containing_message.export_path
            return ImportedSymbol(
                c_import.name + "." + self.pythonic_name, c_import.import_path
            )
        return ImportedSymbol(self.pythonic_name, self.containing_file.export_path)

    @property
    def pb2(self) -> ImportedSymbol:
        if self.containing_message is not None:
            c_import = self.containing_message.pb2
            return ImportedSymbol(c_import.name + "." + self.name, c_import.import_path)
        return ImportedSymbol(self.name, self.containing_file.pb2)


class Field(Descriptor):
    def __init__(
        self,
        descriptor: pb.FieldDescriptorProto,
        containing_message: "Message",
        containing_file: "File",
        index: int = -1,
    ) -> None:
        self.descriptor = descriptor
        self.containing_message = containing_message
        self._pythonic_name = ""
        self._containing_file = containing_file
        self._oneof: "OneOf|None|bool" = None
        self._index = index
        self._path_in_file: Sequence[int] | None = None
        self._settings = FieldPySDKSettings(
            descriptor.options.Extensions[field_py_sdk]  # type: ignore
        )

    @property
    def source_info(self) -> SourceInfo:
        if self.path_in_file in self._containing_file.source_code_info:
            return SourceInfo(self._containing_file.source_code_info[self.path_in_file])
        return SourceInfo()

    @property
    def path_in_file(self) -> Sequence[int]:
        if self._path_in_file is None:
            self._path_in_file = tuple(
                tuple(self.containing_message.path_in_file)
                + tuple(
                    [
                        pb.DescriptorProto.FIELD_FIELD_NUMBER,
                        self._index,
                    ]
                )
            )
        return self._path_in_file

    def is_in_oneof(self) -> bool:
        return self.descriptor.HasField("oneof_index")

    @property
    def containing_oneof(self) -> "OneOf":
        if self._oneof is None:
            if not self.is_in_oneof():
                self._oneof = False
            else:
                self._oneof = self.containing_message.oneofs[
                    self.descriptor.oneof_index
                ]
        if isinstance(self._oneof, OneOf):
            return self._oneof
        raise ValueError("not in OneOf")

    @property
    def full_type_name(self) -> str:
        if self.is_extension():
            return "." + self._containing_file.package + "." + self.name
        return self.containing_message.full_type_name + "." + self.name

    def __repr__(self) -> str:
        return f"Field({self.full_type_name})"

    @property
    def pythonic_name(self) -> str:
        if self._pythonic_name == "":
            try:
                self._pythonic_name = names.field(
                    self.name,
                    self.containing_message.name,
                    self._settings.name,
                    self.full_type_name,
                )
            except names.NameError as e:
                raise DescriptorNameError(self, e) from None
        return self._pythonic_name

    @property
    def message(self) -> "Message":
        if self.descriptor.type == self.descriptor.TYPE_MESSAGE:
            return self.containing_message.get_message_by_type_name(
                self.descriptor.type_name
            )
        else:
            raise FieldNotMessageError(self)

    @property
    def enum(self) -> "Enum":
        if self.descriptor.type == self.descriptor.TYPE_ENUM:
            return self.containing_message.get_enum_by_type_name(
                self.descriptor.type_name
            )
        else:
            raise FieldNotEnumError(self)

    def tracks_presence(self) -> bool:
        return (  # type:ignore[no-any-return,unused-ignore]
            self.descriptor.proto3_optional
            or (
                self.descriptor.type == self.descriptor.TYPE_MESSAGE
                and self.descriptor.label != self.descriptor.LABEL_REPEATED
            )
            or self.descriptor.HasField("oneof_index")
        )

    def is_extension(self) -> bool:
        return self.descriptor.extendee != ""

    @property
    def pb2(self) -> ImportedSymbol:
        if self.is_extension():
            return ImportedSymbol(
                self.name,
                self._containing_file.pb2,
            )
        else:
            msg_pb2 = self.containing_message.pb2
            return ImportedSymbol(msg_pb2.name + "." + self.name, msg_pb2.import_path)

    @property
    def export_path(self) -> ImportedSymbol:
        if self.is_extension():
            return ImportedSymbol(
                self.pythonic_name,
                self._containing_file.export_path,
            )
        else:
            msg = self.containing_message.export_path
            return ImportedSymbol(msg.name + "." + self.pythonic_name, msg.import_path)

    @property
    def number(self) -> int:
        return self.descriptor.number

    @property
    def map_key(self) -> "Field":
        return self.message.field_by_name("key")

    @property
    def map_value(self) -> "Field":
        return self.message.field_by_name("value")

    def python_type(self) -> ImportedSymbol:
        match self.descriptor.type:
            case self.descriptor.TYPE_DOUBLE | self.descriptor.TYPE_FLOAT:
                return ImportedSymbol("float", "builtins")
            case (
                self.descriptor.TYPE_INT64
                | self.descriptor.TYPE_UINT64
                | self.descriptor.TYPE_INT32
                | self.descriptor.TYPE_UINT32
                | self.descriptor.TYPE_FIXED64
                | self.descriptor.TYPE_FIXED32
                | self.descriptor.TYPE_SFIXED32
                | self.descriptor.TYPE_SFIXED64
                | self.descriptor.TYPE_SINT32
                | self.descriptor.TYPE_SINT64
            ):
                return ImportedSymbol("int", "builtins")
            case self.descriptor.TYPE_BOOL:
                return ImportedSymbol("bool", "builtins")
            case self.descriptor.TYPE_STRING:
                return ImportedSymbol("str", "builtins")
            case self.descriptor.TYPE_BYTES:
                return ImportedSymbol("bytes", "builtins")
            case self.descriptor.TYPE_ENUM:
                return self.enum.export_path
            case self.descriptor.TYPE_MESSAGE:
                return self.message.export_path
            case _:
                raise ValueError(f"Unsupported descriptor type: {self.descriptor.type}")

    def is_enum(self) -> bool:
        if self.descriptor.type == self.descriptor.TYPE_ENUM:
            return True
        return False

    def is_map(self) -> bool:
        return (
            self.descriptor.label == self.descriptor.LABEL_REPEATED
            and self.descriptor.type == self.descriptor.TYPE_MESSAGE
            and self.message.is_map_entry()
        )

    def is_repeated(self) -> bool:
        return (
            self.descriptor.label == self.descriptor.LABEL_REPEATED
            and not self.is_map()
        )

    def is_message(self) -> bool:
        if self.descriptor.type == self.descriptor.TYPE_MESSAGE:
            return True
        return False


class OneOf(Descriptor):
    def __init__(
        self,
        descriptor: pb.OneofDescriptorProto,
        index: int,
        containing_message: "Message",
        containing_file: "File",
    ) -> None:
        self.descriptor = descriptor
        self.containing_message = containing_message
        self._index = index
        self._pythonic_name = ""
        self._containing_file = containing_file
        self._fields: "list[Field]|None" = None
        self._path_in_file: Sequence[int] | None = None
        self._settings = OneofPySDKSettings(
            descriptor.options.Extensions[oneof_py_sdk]  # type: ignore
        )

    @property
    def source_info(self) -> SourceInfo:
        if self.path_in_file in self._containing_file.source_code_info:
            return SourceInfo(self._containing_file.source_code_info[self.path_in_file])
        return SourceInfo()

    @property
    def path_in_file(self) -> Sequence[int]:
        if self._path_in_file is None:
            self._path_in_file = tuple(
                tuple(self.containing_message.path_in_file)
                + tuple(
                    [
                        pb.DescriptorProto.ONEOF_DECL_FIELD_NUMBER,
                        self._index,
                    ]
                )
            )
        return self._path_in_file

    @property
    def fields(self) -> list[Field]:
        if self._fields is None:
            self._fields = [
                f
                for f in self.containing_message.fields()
                if (
                    f.descriptor.HasField("oneof_index")
                    and f.descriptor.oneof_index == self._index
                )
            ]
        return self._fields

    @property
    def full_type_name(self) -> str:
        return self.containing_message.full_type_name + "." + self.name

    def __repr__(self) -> str:
        return f"OneOf({self.full_type_name})"

    @property
    def pythonic_name(self) -> str:
        if self._pythonic_name == "":
            try:
                self._pythonic_name = names.one_of(
                    self.name,
                    self.containing_message.name,
                    self._settings.name,
                    self.full_type_name,
                )
            except names.NameError as e:
                raise DescriptorNameError(self, e) from None
        return self._pythonic_name

    @property
    def export_path(self) -> ImportedSymbol:
        msg = self.containing_message.export_path
        return ImportedSymbol(msg.name + "." + self.pythonic_name, msg.import_path)


class Message(Descriptor):
    def __init__(
        self,
        descriptor: pb.DescriptorProto,
        containing_file: "File",
        containing_message: "Message|None" = None,
        index: int = -1,
    ) -> None:
        self.descriptor = descriptor
        self.containing_file = containing_file
        self.containing_message = containing_message
        self._messages: "list[Message]|None" = None
        self._messages_dict: "dict[str,Message]|None" = None
        self._fields: list[Field] | None = None
        self._fields_dict: dict[str, Field] | None = None
        self._enums_dict: dict[str, Enum] | None = None
        self._oneofs: list[OneOf] | None = None
        self._oneofs_dict: dict[str, OneOf] | None = None
        self.attached_names = dict[str, str]()
        self._pythonic_name = ""
        self._index = index
        self._path_in_file: Sequence[int] | None = None
        self._settings = MessagePySDKSettings(
            descriptor.options.Extensions[message_py_sdk]  # type: ignore
        )
        self._checked = False

    def check_names(self) -> None:
        if self._checked:
            return
        val_names = defaultdict[str, list[Descriptor]](list[Descriptor])
        inner_errors: list[DuplicatesError] = []
        for field in self.fields():
            val_names[field.pythonic_name].append(field)
        for msg in self.messages():
            val_names[msg.pythonic_name].append(msg)
            try:
                msg.check_names()
            except DuplicatesError as e:
                inner_errors.append(e)
        for enum in self.enums:
            val_names[enum.pythonic_name].append(enum)
            try:
                enum.check_names()
            except DuplicatesError as e:
                inner_errors.append(e)
        for oneof in self.oneofs:
            val_names[oneof.pythonic_name].append(oneof)
        duplicates: list[list[Descriptor]] = [
            v for v in val_names.values() if len(v) > 1
        ]
        if duplicates or len(inner_errors) > 0:
            raise DuplicatesError(self, duplicates, inner_errors)
        self._checked = True

    @property
    def source_info(self) -> SourceInfo:
        if self.path_in_file in self.containing_file.source_code_info:
            return SourceInfo(self.containing_file.source_code_info[self.path_in_file])
        return SourceInfo()

    @property
    def path_in_file(self) -> Sequence[int]:
        if self._path_in_file is None:
            if self.containing_message is not None:
                self._path_in_file = tuple(
                    tuple(self.containing_message.path_in_file)
                    + tuple(
                        [
                            pb.DescriptorProto.NESTED_TYPE_FIELD_NUMBER,
                            self._index,
                        ]
                    )
                )
            else:
                self._path_in_file = tuple(
                    [
                        pb.FileDescriptorProto.MESSAGE_TYPE_FIELD_NUMBER,
                        self._index,
                    ]
                )
        return self._path_in_file

    def __repr__(self) -> str:
        return f"Message({self.full_type_name})"

    @property
    def pythonic_name(self) -> str:
        if self._pythonic_name == "":
            try:
                self._pythonic_name = names.message(
                    self.full_type_name,
                    self._settings.name,
                )
            except names.NameError as e:
                raise DescriptorNameError(self, e) from None
        return self._pythonic_name

    @property
    def enums_dict(self) -> dict[str, Enum]:
        if self._enums_dict is None:
            self._enums_dict = {
                e.name: Enum(e, self.containing_file, self, index=i)
                for i, e in enumerate(self.descriptor.enum_type)
            }
        return self._enums_dict

    @property
    def oneofs(self) -> list[OneOf]:
        if self._oneofs is None:
            self._oneofs = [
                OneOf(o, i, self, self.containing_file)
                for i, o in enumerate(self.descriptor.oneof_decl)
            ]
        return self._oneofs

    @property
    def oneofs_dict(self) -> dict[str, OneOf]:
        if self._oneofs_dict is None:
            self._oneofs_dict = {o.name: o for o in self.oneofs}
        return self._oneofs_dict

    @property
    def enums(self) -> Iterable[Enum]:
        return self.enums_dict.values()

    @property
    def fields_dict(self) -> dict[str, Field]:
        if self._fields_dict is None:
            self._fields_dict = {field.name: field for field in self.fields()}
        return self._fields_dict

    @property
    def no_wrap(self) -> bool:
        if self.containing_file.skipped:
            return True
        return False

    @property
    def export_path(self) -> ImportedSymbol:
        if self.containing_message is not None:
            c_import = self.containing_message.export_path
            return ImportedSymbol(
                c_import.name + "." + self.pythonic_name, c_import.import_path
            )
        return ImportedSymbol(self.pythonic_name, self.containing_file.export_path)

    def field_by_name(self, name: str) -> Field:
        return self.fields_dict[name]

    def fields(self) -> list[Field]:
        if self._fields is None:
            self._fields = [
                Field(f, self, self.containing_file, index=i)
                for i, f in enumerate(self.descriptor.field)
            ]
        return self._fields

    @property
    def full_type_name(self) -> str:
        if self.containing_message is not None:
            return self.containing_message.full_type_name + "." + self.name
        return "." + self.containing_file.package + "." + self.name

    def get_message_by_type_name(self, name: str, strict: bool = False) -> "Message":
        if name[0] == ".":
            return self.containing_file.get_message_by_type_name(name)
        name_parts = name.split(".", 1)
        try:
            msg = self.message_by_name(name_parts[0])
            if len(name_parts) > 1:
                return msg.get_message_by_type_name(name_parts[1], strict=True)
            return msg
        except KeyError:
            if strict:
                raise KeyError(
                    f"Message {name} not found in scope of " f"{self.full_type_name}"
                )
            if self.containing_message is not None:
                return self.containing_message.get_message_by_type_name(name)
            else:
                return self.containing_file.get_message_by_type_name(name)

    def get_enum_by_type_name(self, name: str, strict: bool = False) -> "Enum":
        if name[0] == ".":
            return self.containing_file.get_enum_by_type_name(name)
        name_parts = name.split(".", 1)
        try:
            if len(name_parts) > 1:
                msg = self.message_by_name(name_parts[0])
                return msg.get_enum_by_type_name(name_parts[1], strict=True)
            return self.enums_dict[name_parts[0]]
        except KeyError:
            if strict:
                raise KeyError(
                    f"Enum {name} not found in scope of " f"{self.full_type_name}"
                )
            if self.containing_message is not None:
                return self.containing_message.get_enum_by_type_name(name)
            else:
                return self.containing_file.get_enum_by_type_name(name)

    def message_by_name(self, name: str) -> "Message":
        if self._messages_dict is None:
            self._messages_dict = {msg.name: msg for msg in self.messages()}
        return self._messages_dict[name]

    def messages(self) -> Sequence["Message"]:
        if self._messages is None:
            self._messages = [
                Message(msg, self.containing_file, self, index=i)
                for i, msg in enumerate(self.descriptor.nested_type)
            ]
        return self._messages

    def is_map_entry(self) -> bool:
        if self.descriptor.options.map_entry:
            return True
        return False

    @property
    def pb2(self) -> ImportedSymbol:
        if self.containing_message is not None:
            c_import = self.containing_message.pb2
            return ImportedSymbol(c_import.name + "." + self.name, c_import.import_path)
        return ImportedSymbol(self.name, self.containing_file.pb2)

    def collect_all_names(self) -> set[str]:
        ret = set[str]([field.pythonic_name for field in self.fields()])
        for msg in self.messages():
            ret.add(msg.pythonic_name)
            ret = ret.union(msg.collect_all_names())
        for enum in self.enums:
            ret.add(enum.pythonic_name)
            ret = ret.union([v.pythonic_name for v in enum.values])
        for oneof in self.oneofs:
            ret.add(oneof.pythonic_name)
        return ret


class Method(Descriptor):
    def __init__(
        self,
        descriptor: pb.MethodDescriptorProto,
        containing_service: "Service",
        index: int = -1,
    ) -> None:
        self.descriptor = descriptor
        self.containing_service = containing_service
        self._pythonic_name = ""
        self._input: Message | None = None
        self._output: Message | None = None
        self._index = index
        self._path_in_file: Sequence[int] | None = None
        self._settings = MethodPySDKSettings(
            self.descriptor.options.Extensions[method_py_sdk]  # type: ignore
        )

    @property
    def source_info(self) -> SourceInfo:
        if (
            self.path_in_file
            in self.containing_service.containing_file.source_code_info
        ):
            return SourceInfo(
                self.containing_service.containing_file.source_code_info[
                    self.path_in_file
                ]
            )
        return SourceInfo()

    @property
    def path_in_file(self) -> Sequence[int]:
        if self._path_in_file is None:
            self._path_in_file = tuple(
                tuple(self.containing_service.path_in_file)
                + tuple(
                    [
                        pb.ServiceDescriptorProto.METHOD_FIELD_NUMBER,
                        self._index,
                    ]
                )
            )
        return self._path_in_file

    def __repr__(self) -> str:
        return f"Method({self.full_type_name})"

    @property
    def input(self) -> Message:
        if self._input is None:
            self._input = (
                self.containing_service.containing_file.get_message_by_type_name(
                    self.descriptor.input_type
                )
            )
        return self._input

    @property
    def output(self) -> Message:
        if self._output is None:
            self._output = (
                self.containing_service.containing_file.get_message_by_type_name(
                    self.descriptor.output_type
                )
            )
        return self._output

    @property
    def full_type_name(self) -> str:
        return self.containing_service.full_type_name + "." + self.name

    @property
    def pythonic_name(self) -> str:
        if self._pythonic_name == "":
            try:
                self._pythonic_name = names.method(
                    self.name,
                    self.containing_service.pythonic_name,
                    self._settings.name,
                    self.full_type_name,
                )
            except names.NameError as e:
                raise DescriptorNameError(self, e) from None
        return self._pythonic_name


class Service(Descriptor):
    def __init__(
        self,
        descriptor: pb.ServiceDescriptorProto,
        containing_file: "File",
        index: int = -1,
    ) -> None:
        self.descriptor = descriptor
        self.containing_file = containing_file
        self._pythonic_name = ""
        self._methods: dict[str, Method] | None = None
        self._index = index
        self._path_in_file: Sequence[int] | None = None
        self._settings = ServicePySDKSettings(
            self.descriptor.options.Extensions[service_py_sdk]  # type: ignore
        )
        self._checked = False

    def check_names(self) -> None:
        if self._checked:
            return

        val_names = defaultdict[str, list[Descriptor]](list[Descriptor])
        for method in self.methods.values():
            val_names[method.pythonic_name].append(method)
        duplicates: list[list[Descriptor]] = [
            v for v in val_names.values() if len(v) > 1
        ]
        if duplicates:
            raise DuplicatesError(self, duplicates)
        self._checked = True

    @property
    def source_info(self) -> SourceInfo:
        if self.path_in_file in self.containing_file.source_code_info:
            return SourceInfo(self.containing_file.source_code_info[self.path_in_file])
        return SourceInfo()

    @property
    def path_in_file(self) -> Sequence[int]:
        if self._path_in_file is None:
            self._path_in_file = tuple(
                [
                    pb.FileDescriptorProto.SERVICE_FIELD_NUMBER,
                    self._index,
                ]
            )
        return self._path_in_file

    def __repr__(self) -> str:
        return f"Service({self.full_type_name})"

    @property
    def methods(self) -> dict[str, Method]:
        if self._methods is None:
            self._methods = {
                m.name: Method(m, self, index=i)
                for i, m in enumerate(self.descriptor.method)
            }
        return self._methods

    @property
    def export_path(self) -> ImportedSymbol:
        return ImportedSymbol(self.pythonic_name, self.containing_file.export_path)

    @property
    def pythonic_name(self) -> str:
        if self._pythonic_name == "":
            try:
                self._pythonic_name = names.service(
                    self.full_type_name,
                    self._settings.name,
                )
            except names.NameError as e:
                raise DescriptorNameError(self, e) from None
        return self._pythonic_name

    @property
    def full_type_name(self) -> str:
        return "." + self.containing_file.package + "." + self.name

    def collect_all_names(self) -> set[str]:
        ret = set[str]([m.pythonic_name for m in self.methods.values()])
        return ret


class File(Descriptor):
    def __init__(
        self,
        descriptor: pb.FileDescriptorProto,
        file_set: "FileSet",
        is_generated: bool,
    ) -> None:
        self.descriptor = descriptor
        self.global_set = file_set
        self.is_generated = is_generated
        import_path = (
            self.descriptor.name.removesuffix(".proto").replace("/", ".") + "_pb2"
        )
        for prefix, subst in file_set.import_substitutions.items():
            if import_path.startswith(prefix + ".") or import_path == prefix:
                import_path = subst + import_path.removeprefix(prefix)
                break
        self.pb2: ImportPath = ImportPath(import_path)
        self.skipped: bool = self.global_set.is_package_skipped(self.package)
        if self.skipped:
            self.export_path: ImportPath = self.pb2
        else:
            export_path = self.descriptor.package
            export_substituted = False
            for prefix, subst in file_set.export_substitutions.items():
                if export_path.startswith(prefix + ".") or export_path == prefix:
                    export_path = subst + export_path.removeprefix(prefix)
                    export_substituted = True
                    break
            if not export_substituted:
                for prefix, subst in file_set.import_substitutions.items():
                    if export_path.startswith(prefix + ".") or export_path == prefix:
                        export_path = subst + export_path.removeprefix(prefix)
                        break
            self.export_path = ImportPath(export_path)
        self._messages: list[Message] | None = None
        self._messages_dict: dict[str, Message] | None = None
        self._deps_dict: dict[str, File] | None = None
        self._enums_dict: dict[str, Enum] | None = None
        self._services_dict: dict[str, Service] | None = None
        self._extensions: dict[str, Field] | None = None
        self._source_code_info: (
            dict[Sequence[int], pb.SourceCodeInfo.Location] | None
        ) = None
        self._checked: defaultdict[str, list[Descriptor]] | None = None

    def check_names(self) -> defaultdict[str, list[Descriptor]]:
        if self._checked is not None:
            return self._checked
        val_names = defaultdict[str, list[Descriptor]](list[Descriptor])
        inner_errors = list[DuplicatesError]()
        for srv in self.services_dict.values():
            val_names[srv.pythonic_name].append(srv)
            try:
                srv.check_names()
            except DuplicatesError as e:
                inner_errors.append(e)
        for msg in self.messages():
            val_names[msg.pythonic_name].append(msg)
            try:
                msg.check_names()
            except DuplicatesError as e:
                inner_errors.append(e)
        for enum in self.enums:
            val_names[enum.pythonic_name].append(enum)
            try:
                enum.check_names()
            except DuplicatesError as e:
                inner_errors.append(e)
        for ext in self.extensions.values():
            val_names[ext.pythonic_name].append(ext)

        duplicates: list[list[Descriptor]] = [
            v for v in val_names.values() if len(v) > 1
        ]
        if duplicates or len(inner_errors) > 0:
            raise DuplicatesError(self, duplicates, inner_errors)
        self._checked = val_names
        return self._checked

    @property
    def source_code_info(self) -> dict[Sequence[int], pb.SourceCodeInfo.Location]:
        if self._source_code_info is None:
            self._source_code_info = {
                tuple(loc.path): loc
                for loc in self.descriptor.source_code_info.location
            }
        return self._source_code_info

    def __repr__(self) -> str:
        return f"File({self.name})"

    @property
    def extensions(self) -> dict[str, Field]:
        if self._extensions is None:
            self._extensions = {
                x.name: Field(
                    x,
                    self.get_message_by_type_name(x.extendee),
                    self,
                )
                for x in self.descriptor.extension
            }
        return self._extensions

    def collect_all_names(self, with_locals: bool = True) -> set[str]:
        ret = set[str](self.package.split("."))
        for msg in self.messages():
            ret.add(msg.pythonic_name)
            if with_locals:
                ret = ret.union(msg.collect_all_names())
        for enum in self.enums:
            ret.add(enum.pythonic_name)
            ret = ret.union([v.pythonic_name for v in enum.values])
        for srv in self.services_dict.values():
            ret.add(srv.pythonic_name)
            ret = ret.union(srv.collect_all_names())
        for ext in self.extensions.values():
            ret.add(ext.pythonic_name)
        if with_locals:
            for dep in self.dependencies.values():
                ret = ret.union(dep.collect_all_names(True))
        return ret

    def get_message_by_type_name(self, name: str, strict: bool = False) -> "Message":
        name_partial = name
        if name_partial[0] == ".":
            if name_partial.startswith("." + self.package + "."):
                strict = True
                name_partial = name_partial.removeprefix("." + self.package + ".")
        name_parts = name_partial.split(".", 1)
        try:
            msg = self.message_by_name(name_parts[0])
            if len(name_parts) > 1:
                return msg.get_message_by_type_name(name_parts[1], strict=True)
            return msg
        except KeyError:
            for dep in self.dependencies.values():
                if (
                    strict
                    and dep.package != self.package
                    and not dep.package.startswith(self.package + ".")
                ):
                    continue
                try:
                    return dep.get_message_by_type_name(name)
                except KeyError:
                    pass
            raise KeyError(f"Message {name} not found in scope of {self.name}")

    def get_enum_by_type_name(self, name: str, strict: bool = False) -> "Enum":
        name_partial = name
        if name_partial[0] == ".":
            if name_partial.startswith("." + self.package + "."):
                strict = True
                name_partial = name_partial.removeprefix("." + self.package + ".")
        name_parts = name_partial.split(".", 1)
        try:
            if len(name_parts) > 1:
                msg = self.message_by_name(name_parts[0])
                return msg.get_enum_by_type_name(name_parts[1], strict=True)
            return self.enums_dict[name_parts[0]]
        except KeyError:
            for dep in self.dependencies.values():
                if (
                    strict
                    and dep.package != self.package
                    and not dep.package.startswith(self.package + ".")
                ):
                    continue
                try:
                    return dep.get_enum_by_type_name(name)
                except KeyError:
                    pass
            raise KeyError(f"Enum {name} not found in scope of {self.name}")

    @property
    def dependencies(self) -> "dict[str, File]":
        if self._deps_dict is None:
            self._deps_dict = {
                name: self.global_set.file_by_name(name)
                for name in self.descriptor.dependency
            }
        return self._deps_dict

    @property
    def package(self) -> str:
        return str(self.descriptor.package)

    def get_field_by_type_name(self, full_field_name: str) -> Field:
        msg_name, field_name = full_field_name.rsplit(".", 2)
        msg = self.get_message_by_type_name(msg_name)
        return msg.field_by_name(field_name)

    def get_extension_by_type_name(self, name: str, strict: bool = False) -> Field:
        name_partial = name
        if name_partial[0] == ".":
            if name_partial.startswith("." + self.package + "."):
                strict = True
                name_partial = name_partial.removeprefix("." + self.package + ".")
        try:
            return self.extensions[name_partial]
        except KeyError:
            for dep in self.dependencies.values():
                if (
                    strict
                    and dep.package != self.package
                    and not dep.package.startswith(self.package + ".")
                ):
                    continue
                try:
                    return dep.get_extension_by_type_name(name)
                except KeyError:
                    pass
            raise KeyError(f"Extension {name} not found in scope of {self.name}")

    def message_by_name(self, name: str) -> Message:
        if self._messages_dict is None:
            self._messages_dict = {msg.name: msg for msg in self.messages()}
        return self._messages_dict[name]

    def messages(self) -> Sequence[Message]:
        if self._messages is None:
            self._messages = [
                Message(msg, self, index=i)
                for i, msg in enumerate(self.descriptor.message_type)
            ]
        return self._messages

    @property
    def services_dict(self) -> dict[str, Service]:
        if self._services_dict is None:
            self._services_dict = {
                s.name: Service(s, self, index=i)
                for i, s in enumerate(self.descriptor.service)
            }
        return self._services_dict

    @property
    def enums_dict(self) -> dict[str, Enum]:
        if self._enums_dict is None:
            self._enums_dict = {
                e.name: Enum(e, self, index=i)
                for i, e in enumerate(self.descriptor.enum_type)
            }
        return self._enums_dict

    @property
    def enums(self) -> Iterable[Enum]:
        return self.enums_dict.values()

    @property
    def grpc(self) -> ImportPath:
        p = self.pb2
        return ImportPath(p.import_path + "_grpc")


class FileSet(Descriptor):
    def __init__(
        self,
        file_set: Sequence[pb.FileDescriptorProto],
        files_to_generate: Iterable[str],
        import_substitutions: dict[str, str] | None = None,
        export_substitutions: dict[str, str] | None = None,
        skip_packages: list[str] | None = None,
    ):
        if import_substitutions is None:
            import_substitutions = dict[str, str]()
        if export_substitutions is None:
            export_substitutions = dict[str, str]()
        if skip_packages is None:
            skip_packages = list[str]()

        self.import_substitutions = import_substitutions
        self.export_substitutions = export_substitutions
        self.skip_packages = set(skip_packages)
        self.files_to_generate = frozenset(files_to_generate)

        self._file_set = [
            File(file, self, file.name in self.files_to_generate) for file in file_set
        ]
        self._files_dict: dict[str, File] | None = None
        self._checked = False

    def check_names(self) -> None:
        if self._checked:
            return

        val_names = defaultdict[str, defaultdict[str, list[Descriptor]]](
            lambda: defaultdict(list[Descriptor])
        )
        inner_errors: list[DuplicatesError] = []
        for file in self.files_generated:
            try:
                file_children = file.check_names()
                for name, child in file_children.items():
                    val_names[file.package][name].extend(child)
            except DuplicatesError as e:
                inner_errors.append(e)
        for pkg_names in val_names.values():
            duplicates = [v for v in pkg_names.values() if len(v) > 1]
            if duplicates:
                inner_errors.append(
                    DuplicatesError(
                        self,
                        duplicates,
                    )
                )
        if inner_errors:
            raise DuplicatesError(self, [], inner_errors)
        self._checked = True

    def is_package_skipped(self, package: str) -> bool:
        for pkg in self.skip_packages:
            if package == pkg or package.startswith(pkg + "."):
                return True
        return False

    def collect_names(self, package: str) -> set[str]:
        ret = set[str](package.split("."))
        for file in self.files:
            if file.package == package:
                ret = ret.union(file.collect_all_names())
        return ret

    def file_by_name(self, name: str) -> "File":
        return self.files_dict[name]

    @property
    def files_dict(self) -> dict[str, File]:
        if self._files_dict is None:
            self._files_dict = {file.name: file for file in self._file_set}
        return self._files_dict

    @property
    def files(self) -> Sequence[File]:
        return self._file_set

    @property
    def files_generated(self) -> Sequence[File]:
        return [f for f in self.files if f.is_generated]
