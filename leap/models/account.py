import pydantic


class XtAccountStatus(pydantic.BaseModel):
    """Account status. 迅投账号状态结构"""

    account_type: int = pydantic.Field(..., description="资金账号类型")
    account_id: str = pydantic.Field(..., description="资金账号")
    status: int = pydantic.Field(..., description="账号状态，详细见账号状态定义")
