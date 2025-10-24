from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class SystemSettings(BaseModel):
    """SystemSettings is a configuration model for the RDEtoolkit system settings.

    Attributes:
        extended_mode (str | None): The mode to run the RDEtoolkit in. Options include 'rdeformat' and 'MultiDataTile'. Default is None.
        save_raw (bool): Indicates whether to automatically save raw data to the raw directory. Default is False.
        save_nonshared_raw (bool): Indicates whether to save nonshared raw data. If True, non-shared raw data will be saved. Default is True.
        save_thumbnail_image (bool): Indicates whether to automatically save the main image to the thumbnail directory. Default is False.
        magic_variable (bool): A feature where specifying '${filename}' as the data name results in the filename being transcribed as the data name. Default is False.
    """

    extended_mode: str | None = Field(default=None, description="The mode to run the RDEtoolkit in. select: rdeformat, MultiDataTile")
    save_raw: bool = Field(default=False, description="Auto Save raw data to the raw directory")
    save_nonshared_raw: bool = Field(default=True, description="Specifies whether to save nonshared raw data. If True, non-shared raw data will be saved.")
    save_thumbnail_image: bool = Field(default=False, description="Auto Save main image to the thumbnail directory")
    magic_variable: bool = Field(
        default=False,
        description="The feature where specifying '${filename}' as the data name results in the filename being transcribed as the data name.",
    )

    @field_validator('extended_mode')
    @classmethod
    def validate_extended_mode(cls, v: str | None) -> str | None:
        """Validate extended_mode to only allow exact matches for 'rdeformat' and 'MultiDataTile'."""
        if v is None:
            return v

        valid_modes = ["rdeformat", "MultiDataTile"]

        if v not in valid_modes:
            error_msg = f'Invalid extended_mode "{v}". Valid options are: {valid_modes}'
            raise ValueError(error_msg)

        return v


class MultiDataTileSettings(BaseModel):
    ignore_errors: bool = Field(default=False, description="If true, errors encountered during processing will be ignored, and the process will continue without stopping.")


class SmartTableSettings(BaseModel):
    """SmartTableSettings is a configuration model for SmartTable processing.

    Attributes:
        save_table_file (bool): Save original SmartTable file (smarttable_*.xlsx/csv/tsv) to raw/nonshared_raw directories. Default is False.
    """
    save_table_file: bool = Field(default=False, description="Save original SmartTable file (smarttable_*.xlsx/csv/tsv) to raw/nonshared_raw directories")


# class ExcelInvoiceSettings(BaseModel):
#     ignore_errors: bool = Field(default=False, description="If true, errors encountered during ExcelInvoice processing will be ignored, and the process will continue without stopping.")


class TracebackSettings(BaseModel):
    """TracebackSettings is a configuration model for compact stacktrace formatting.

    This class defines configuration options for the LLM/AI-friendly traceback formatting system,
    providing control over output format, detail level, and security settings.

    Attributes:
        enabled (bool): Enable compact traceback formatting. Default is False.
        format (str): Output format. Options: "compact", "python", "duplex". Default is "duplex"
        include_context (bool): Include source code context in traceback. Default is True.
        include_locals (bool): Include local variables in traceback. Default is False.
        include_env (bool): Include environment information in traceback. Default is False.
        max_locals_size (int): Maximum size for local variable representation (UTF-8 bytes). Default is 512.
        sensitive_patterns (list[str]): Custom patterns for sensitive information masking. Default is empty.

    """
    enabled: bool = Field(default=False, description="Enable compact traceback formatting")
    format: str = Field(default="duplex", description="Output format: compact, python, duplex")
    include_context: bool = Field(default=False, description="Include source code context")
    include_locals: bool = Field(default=False, description="Include local variables")
    include_env: bool = Field(default=False, description="Include environment info")
    max_locals_size: int = Field(default=512, description="Max size for locals (UTF-8 bytes)")
    sensitive_patterns: list[str] = Field(default_factory=list, description="Custom sensitive patterns")

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate format field to only allow valid output formats."""
        valid_formats = ["compact", "python", "duplex"]
        if v not in valid_formats:
            error_msg = f"Invalid format: '{v}'. Valid options are: {valid_formats}"
            raise ValueError(error_msg)
        return v

    @field_validator('max_locals_size')
    @classmethod
    def validate_max_locals_size(cls, v: int) -> int:
        """Validate max_locals_size to ensure it's a positive integer.

        Provide distinct error messages for negative and zero values so tests
        and callers can distinguish invalid input (negative) from non-positive
        but specific boundary (zero).
        """
        if v < 0:
            emsg = "Invalid max_locals_size"
            raise ValueError(emsg)
        if v == 0:
            emsg = "max_locals_size must be a positive integer"
            raise ValueError(emsg)
        return v


class Config(BaseModel, extra="allow"):
    """The configuration class used in RDEToolKit.

    Attributes:
        system (SystemSettings): System related settings.
        multidata_tile (MultiDataTileSettings | None): MultiDataTile related settings.
        smarttable (SmartTableSettings | None): SmartTable related settings.
        excel_invoice (ExcelInvoiceSettings | None): ExcelInvoice related settings.
    """
    system: SystemSettings = Field(default_factory=SystemSettings, description="System related settings")
    multidata_tile: MultiDataTileSettings | None = Field(default_factory=MultiDataTileSettings, description="MultiDataTile related settings")
    smarttable: SmartTableSettings | None = Field(default=None, description="SmartTable related settings")
    traceback: TracebackSettings | None = Field(default=None, description="Traceback formatting settings")
    # excel_invoice: ExcelInvoiceSettings | None = Field(default_factory=ExcelInvoiceSettings, description="ExcelInvoice related settings")
