import pydantic


class XtAccountStatus(pydantic.BaseModel):
    """Account status.

    迅投账号状态结构

    Attributes:
        account_type: int, 资金账号类型
        account_id: str, 资金账号
        status: int, 账号状态，详细见账号状态定义
    """
    account_type: int
    account_id: str
    status: int