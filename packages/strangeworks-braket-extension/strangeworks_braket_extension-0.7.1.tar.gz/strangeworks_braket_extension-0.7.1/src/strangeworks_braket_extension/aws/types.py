"""types.py."""

import os

from pydantic import AliasChoices, BaseModel, Field
from strangeworks_extensions.plugins.instrumentation import Instrumentation

AWS_KEY_ID = "AWS_ACCESS_KEY_ID"
AWS_KEY = "AWS_SECRET_ACCESS_KEY"
S3_BUCKET_NAME = "AMZN_BRAKET_OUT_S3_BUCKET"


class BraketConfig(BaseModel):
    """_summary_

    Parameters
    ----------
    BaseModel : _type_
        _description_

    Attributes
    ----------
    aws_access_key_id: str
        AWS_ACCESS_KEY_ID env var
    aws_secret_access_key: str
        AWS_SECRET_ACCESS_KEY env var
    s3_bucket: str
        AMZN_BRAKET_OUT_S3_BUCKET env var. Should be the name
        (amazon-braket-us-west-2-res_id) only and not
        the ARN (not arn:aws:s3:::amazon-braket-us-west-2-wvr9pai22)
    """

    aws_access_key_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices(AWS_KEY_ID, "aws_access_key_id"),
    )
    aws_secret_access_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(AWS_KEY, "aws_secret_access_key"),
    )
    s3_bucket_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices(S3_BUCKET_NAME, "s3_bucket_name"),
    )

    def setenv(self):
        if self.aws_access_key_id:
            os.environ[AWS_KEY_ID] = self.aws_access_key_id
        if self.aws_secret_access_key:
            os.environ[AWS_KEY] = self.aws_secret_access_key
        if self.s3_bucket_name:
            os.environ[S3_BUCKET_NAME] = self.s3_bucket_name

    def is_complete(self) -> bool:
        """Checks if all configuration attributes are set."""
        return (
            self.aws_access_key_id is not None
            and self.aws_secret_access_key is not None
            and self.s3_bucket_name is not None
        )

    @classmethod
    def from_env(cls):
        """Create BraketConfig Object from Environment Variables"""
        args: dict[str, str] = {}
        if AWS_KEY_ID in os.environ:
            args[AWS_KEY_ID] = os.environ[AWS_KEY_ID]
        if AWS_KEY in os.environ:
            args[AWS_KEY] = os.environ[AWS_KEY]
        if S3_BUCKET_NAME in os.environ:
            args[S3_BUCKET_NAME] = os.environ[S3_BUCKET_NAME]
        return cls(**args)


class BraketServerless(Instrumentation):
    def __init__(
        self,
        braket_cfg: BraketConfig | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.sw_braket_cfg: BraketConfig | None = braket_cfg
        self._env_backup: BraketConfig | None = None
        self.sw_cfg_enabled: bool = False

    def _enable_sworks_cfg(self):
        """Setup Braket Environment Variables.

        If a BraketConfig object is set,
        O if a configuration was provided.
        """
        if self.sw_braket_cfg and self.sw_braket_cfg.is_complete():
            self._env_backup = BraketConfig.from_env()
            self.sw_braket_cfg.setenv()
            self.sw_cfg_enabled = True

    def _disable_sworks_cfg(self):
        """Rollback Braket environment variables"""
        if self.sw_cfg_enabled:
            if self._env_backup:
                self._env_backup.setenv()
                self._env_backup = None
            self.sw_cfg_enabled = False

    def enable(self, *args, **kwargs):
        self._enable_sworks_cfg()
        return super().enable(*args, **kwargs)

    def disable(self, *args, **kwargs):
        self._disable_sworks_cfg()
        return super().disable(*args, **kwargs)
