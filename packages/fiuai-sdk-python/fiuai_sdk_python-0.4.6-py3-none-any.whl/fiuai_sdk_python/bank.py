# -- coding: utf-8 --
# Project: fiuaiclient
# Created Date: 2025 06 Fr
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI



from pydantic import BaseModel, Field
import logging
from .type import BankAccount
from .client import FiuaiSDK
from typing import Literal, Optional

logger = logging.getLogger(__name__)


class CompanyBankAccountSearchResult(BaseModel):
    bank_account_id: str = Field(description="银行账号id", default="")
    bank_account_no: str = Field(description="银行账号", default="")
    bank_account_name: str = Field(description="银行账号", default="")
    bank_id: str = Field(description="银行id", default="")
    bank_name: str = Field(description="银行名称", default="")
    opening_bank_branch_id: str = Field(description="开户行id", default="")
    opening_bank_branch_name: str = Field(description="开户行名称", default="")


    exists: bool = Field(description="是否存在", default=False)

    comment: str = Field(description="备注", default="")


def get_bank_account(client: FiuaiSDK, bank_account_no: str) -> Optional[CompanyBankAccountSearchResult]:
    """
    根据银行账号获取银行账号信息
    
    Args:
        back_account: 银行账号
        
    Returns:
        CompanyBankAccountSearchResult: 银行账号信息
    """

    if not bank_account_no:
        logger.error(f"bank_account_no is empty, return None")
        return None
    
    _bank_account_response = client.internal_get(
        doctype="Bank Account",
        name=bank_account_no,
        fields=["name","bank_account_no", "account_name", "bank", "opening_bank_branch"]
    )

    
    if not _bank_account_response.is_success():
        return CompanyBankAccountSearchResult(exists=False)
    
    _bank_account = _bank_account_response.data
    if not _bank_account:
        return CompanyBankAccountSearchResult(exists=False)
    

    # 获取银行信息
    _bank_detail_response = client.internal_get(
        doctype="Bank",
        name=_bank_account["bank"],
        fields=["name", "bank_name"]
    )
    if not _bank_detail_response.is_success():
        return CompanyBankAccountSearchResult(exists=False)
    
    _bank_detail = _bank_detail_response.data
    if not _bank_detail:
        logger.error(f"bank is not found by id {_bank_account["bank"]}")
        return CompanyBankAccountSearchResult(exists=False)
    
    # 获取支行信息
    _bank_branch_response = client.internal_get(
        doctype="Bank Branch",
        name=_bank_account["opening_bank_branch"],
        fields=["name", "bank_branch_name"]
    )
    if not _bank_branch_response.is_success():
        return CompanyBankAccountSearchResult(exists=False)
    
    _bank_branch = _bank_branch_response.data
    if not _bank_branch:
        logger.error(f"bank branch is not found by id {_bank_account["opening_bank_branch"]}")
        return CompanyBankAccountSearchResult(exists=False)
    
    return CompanyBankAccountSearchResult(
        exists=True, 
        bank_account_id=_bank_account["name"], 
        bank_account_no=_bank_account["bank_account_no"],
        bank_account_name=_bank_account["account_name"],
        bank_id=_bank_account["name"], 
        bank_name=_bank_detail["bank_name"],
        opening_bank_branch_id=_bank_branch["name"],
        opening_bank_branch_name=_bank_branch["bank_branch_name"]
    )


def get_bank_account_by_bank_id(client: FiuaiSDK, bank_id: str) -> BankAccount|None:
    """
    根据银行账号id获取银行账号信息
    """
    resp_response = client.internal_get_list(
            doctype="Bank Account",
            filters=[["name", "=", bank_id]],
            fields=[
                "name",
                "account_name",
                "bank",
                "bank_account_no",
                "opening_bank_branch",
            ],
        )

    if not resp_response.is_success():
        return None
    
    resp = resp_response.data
    if not resp:
        return None
    
    resp = resp[0]

    # 获取支行信息
    bank_branch = ""
    if resp["opening_bank_branch"] != "":
        _bank_branch_response = client.internal_get(
            doctype="Bank Branch",
            name=resp["opening_bank_branch"],
            fields=["name", "bank_branch_name"]
        )
        if not _bank_branch_response.is_success():
            return None
        
        _bank_branch = _bank_branch_response.data
        if not _bank_branch:
            logger.error(f"bank branch is not found by id {resp["opening_bank_branch"]}")
            return None
        else:
            bank_branch = _bank_branch["bank_branch_name"]

    # 获取银行信息
    _bank_detail_response = client.internal_get(
        doctype="Bank",
        name=resp["bank"],
        fields=["name", "bank_name"]
    )

    if not _bank_detail_response.is_success():
        return None
    
    _bank_detail = _bank_detail_response.data
    if not _bank_detail:
        logger.error(f"bank is not found by id {resp["bank"]}")
        return None

    _bank_account = resp
    return BankAccount(
        name=_bank_account["name"],
        account_name=_bank_account.get("account_name", "") if _bank_account.get("account_name", "") else "",
        bank=_bank_detail["bank_name"],
        bank_account_no=_bank_account["bank_account_no"] if _bank_account["bank_account_no"] else "",
        bank_branch=bank_branch,
    )