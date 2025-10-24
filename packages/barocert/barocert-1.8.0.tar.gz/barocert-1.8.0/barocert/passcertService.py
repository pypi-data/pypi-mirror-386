# -*- coding: utf-8 -*-

from .base import BaseService, BarocertException
from .util import String

class PasscertService(BaseService):

    def __init__(self, LinkID, SecretKey, timeOut=15):
        """ 생성자.
            args
                LinkID : 링크허브에서 발급받은 LinkID
                SecretKey : 링크허브에서 발급받은 SecretKey
        """
        super(self.__class__, self).__init__(LinkID, SecretKey)
        self._addScope("441")
        self._addScope("442")
        self._addScope("443")
        self._addScope("444")

    # 본인인증 요청
    def requestIdentity(self, clientCode, identity):

        if String.isNullorEmpty(clientCode):
            raise BarocertException(-99999999, "이용기관코드가 입력되지 않았습니다.")
        if False == clientCode.isdigit():
            raise BarocertException(-99999999, "이용기관코드는 숫자만 입력할 수 있습니다.")
        if 12 != len(clientCode):
            raise BarocertException(-99999999, "이용기관코드는 12자 입니다.")
        if String.isNullorEmpty(identity):
            raise BarocertException(-99999999, "본인인증 요청정보가 입력되지 않았습니다.")    
        if String.isNullorEmpty(identity.receiverHP):
            raise BarocertException(-99999999, "수신자 휴대폰번호가 입력되지 않았습니다.")
        if String.isNullorEmpty(identity.receiverName):
            raise BarocertException(-99999999, "수신자 성명이 입력되지 않았습니다.")
        if String.isNullorEmpty(identity.reqTitle):
            raise BarocertException(-99999999, "인증요청 메시지 제목이 입력되지 않았습니다.")
        if String.isNullorEmpty(identity.callCenterNum):
            raise BarocertException(-99999999, "고객센터 연락처가 입력되지 않았습니다.")            
        if String.isNullorEmpty(identity.expireIn):
            raise BarocertException(-99999999, "만료시간이 입력되지 않았습니다.")
        if String.isNullorEmpty(identity.token):
            raise BarocertException(-99999999, "토큰 원문이 입력되지 않았습니다.")
        
        postData = self._stringtify(identity)

        return self._httppost('/PASS/Identity/' + clientCode, postData)

    # 본인인증 상태확인
    def getIdentityStatus(self, clientCode, receiptID):

        if String.isNullorEmpty(clientCode):
            raise BarocertException(-99999999, "이용기관코드가 입력되지 않았습니다.")
        if False == clientCode.isdigit():
            raise BarocertException(-99999999, "이용기관코드는 숫자만 입력할 수 있습니다.")
        if 12 != len(clientCode):
            raise BarocertException(-99999999, "이용기관코드는 12자 입니다.")
        if String.isNullorEmpty(receiptID):
            raise BarocertException(-99999999, "접수아이디가 입력되지 않았습니다.")
        if False == receiptID.isdigit():
            raise BarocertException(-99999999, "접수아이디는 숫자만 입력할 수 있습니다.")
        if 32 != len(receiptID):
            raise BarocertException(-99999999, "접수아이디는 32자 입니다.")
        
        return self._httpget('/PASS/Identity/' + clientCode + '/' + receiptID )
    
    # 본인인증 검증
    def verifyIdentity(self, clientCode, receiptID, identityVerify):

        if String.isNullorEmpty(clientCode):
            raise BarocertException(-99999999, "이용기관코드가 입력되지 않았습니다.")
        if False == clientCode.isdigit():
            raise BarocertException(-99999999, "이용기관코드는 숫자만 입력할 수 있습니다.")
        if 12 != len(clientCode):
            raise BarocertException(-99999999, "이용기관코드는 12자 입니다.")
        if String.isNullorEmpty(receiptID):
            raise BarocertException(-99999999, "접수아이디가 입력되지 않았습니다.")
        if False == receiptID.isdigit():
            raise BarocertException(-99999999, "접수아이디는 숫자만 입력할 수 있습니다.")
        if 32 != len(receiptID):
            raise BarocertException(-99999999, "접수아이디는 32자 입니다.")
        if String.isNullorEmpty(identityVerify):
            raise BarocertException(-99999999, "본인인증 검증 요청 정보가 입력되지 않았습니다.")
        if String.isNullorEmpty(identityVerify.receiverHP):
            raise BarocertException(-99999999, "수신자 휴대폰번호가 입력되지 않았습니다.")
        if String.isNullorEmpty(identityVerify.receiverName):
            raise BarocertException(-99999999, "수신자 성명이 입력되지 않았습니다.")

        postData = self._stringtify(identityVerify)

        return self._httppost('/PASS/Identity/Verify/' + clientCode + '/' + receiptID, postData)

    # 전자서명 요청
    def requestSign(self, clientCode, sign):

        if String.isNullorEmpty(clientCode):
            raise BarocertException(-99999999, "이용기관코드가 입력되지 않았습니다.")
        if False == clientCode.isdigit():
            raise BarocertException(-99999999, "이용기관코드는 숫자만 입력할 수 있습니다.")
        if 12 != len(clientCode):
            raise BarocertException(-99999999, "이용기관코드는 12자 입니다.")
        if String.isNullorEmpty(sign):
            raise BarocertException(-99999999, "전자서명 요청정보가 입력되지 않았습니다.")
        if String.isNullorEmpty(sign.receiverHP):
            raise BarocertException(-99999999, "수신자 휴대폰번호가 입력되지 않았습니다.")
        if String.isNullorEmpty(sign.receiverName):
            raise BarocertException(-99999999, "수신자 성명이 입력되지 않았습니다.")
        if String.isNullorEmpty(sign.reqTitle):
            raise BarocertException(-99999999, "인증요청 메시지 제목이 입력되지 않았습니다.")
        if String.isNullorEmpty(sign.callCenterNum):
            raise BarocertException(-99999999, "고객센터 연락처가 입력되지 않았습니다.")            
        if String.isNullorEmpty(sign.expireIn):
            raise BarocertException(-99999999, "만료시간이 입력되지 않았습니다.")
        if String.isNullorEmpty(sign.token):
            raise BarocertException(-99999999, "토큰 원문이 입력되지 않았습니다.")
        if String.isNullorEmpty(sign.tokenType):
            raise BarocertException(-99999999, "원문 유형이 입력되지 않았습니다.")
        
        postData = self._stringtify(sign)

        return self._httppost('/PASS/Sign/' + clientCode, postData)

    # 전자서명 상태확인
    def getSignStatus(self, clientCode, receiptID):

        if String.isNullorEmpty(clientCode):
            raise BarocertException(-99999999, "이용기관코드가 입력되지 않았습니다.")
        if False == clientCode.isdigit():
            raise BarocertException(-99999999, "이용기관코드는 숫자만 입력할 수 있습니다.")
        if 12 != len(clientCode):
            raise BarocertException(-99999999, "이용기관코드는 12자 입니다.")
        if String.isNullorEmpty(receiptID):
            raise BarocertException(-99999999, "접수아이디가 입력되지 않았습니다.")
        if False == receiptID.isdigit():
            raise BarocertException(-99999999, "접수아이디는 숫자만 입력할 수 있습니다.")
        if 32 != len(receiptID):
            raise BarocertException(-99999999, "접수아이디는 32자 입니다.")

        return self._httpget('/PASS/Sign/' + clientCode + '/' + receiptID)

    # 전자서명 검증
    def verifySign(self, clientCode, receiptID, signVerify):

        if String.isNullorEmpty(clientCode):
            raise BarocertException(-99999999, "이용기관코드가 입력되지 않았습니다.")
        if False == clientCode.isdigit():
            raise BarocertException(-99999999, "이용기관코드는 숫자만 입력할 수 있습니다.")
        if 12 != len(clientCode):
            raise BarocertException(-99999999, "이용기관코드는 12자 입니다.")
        if String.isNullorEmpty(receiptID):
            raise BarocertException(-99999999, "접수아이디가 입력되지 않았습니다.")
        if False == receiptID.isdigit():
            raise BarocertException(-99999999, "접수아이디는 숫자만 입력할 수 있습니다.")
        if 32 != len(receiptID):
            raise BarocertException(-99999999, "접수아이디는 32자 입니다.")
        if String.isNullorEmpty(signVerify):
            raise BarocertException(-99999999, "전자서명 검증 요청 정보가 입력되지 않았습니다.")
        if String.isNullorEmpty(signVerify.receiverHP):
            raise BarocertException(-99999999, "수신자 휴대폰번호가 입력되지 않았습니다.")
        if String.isNullorEmpty(signVerify.receiverName):
            raise BarocertException(-99999999, "수신자 성명이 입력되지 않았습니다.")        

        postData = self._stringtify(signVerify)    

        return self._httppost('/PASS/Sign/Verify/' + clientCode + '/' + receiptID, postData)
    
    # 출금동의 요청
    def requestCMS(self, clientCode, cms):
        
        if String.isNullorEmpty(clientCode):
            raise BarocertException(-99999999, "이용기관코드가 입력되지 않았습니다.")
        if False == clientCode.isdigit():
            raise BarocertException(-99999999, "이용기관코드는 숫자만 입력할 수 있습니다.")
        if 12 != len(clientCode):
            raise BarocertException(-99999999, "이용기관코드는 12자 입니다.")
        if String.isNullorEmpty(cms):
            raise BarocertException(-99999999, "자동이체 출금동의 요청정보가 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.receiverHP):
            raise BarocertException(-99999999, "수신자 휴대폰번호가 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.receiverName):
            raise BarocertException(-99999999, "수신자 성명이 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.reqTitle):
            raise BarocertException(-99999999, "인증요청 메시지 제목이 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.callCenterNum):
            raise BarocertException(-99999999, "고객센터 연락처가 입력되지 않았습니다.")              
        if String.isNullorEmpty(cms.expireIn):
            raise BarocertException(-99999999, "만료시간이 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.bankName):
            raise BarocertException(-99999999, "출금은행명이 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.bankAccountNum):
            raise BarocertException(-99999999, "출금계좌번호가 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.bankAccountName):
            raise BarocertException(-99999999, "출금계좌 예금주명이 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.bankServiceType):
            raise BarocertException(-99999999, "출금 유형이 입력되지 않았습니다.")

        postData = self._stringtify(cms)

        return self._httppost('/PASS/CMS/' + clientCode, postData)

    # 출금동의 상태확인
    def getCMSStatus(self, clientCode, receiptID):

        if String.isNullorEmpty(clientCode):
            raise BarocertException(-99999999, "이용기관코드가 입력되지 않았습니다.")
        if False == clientCode.isdigit():
            raise BarocertException(-99999999, "이용기관코드는 숫자만 입력할 수 있습니다.")
        if 12 != len(clientCode):
            raise BarocertException(-99999999, "이용기관코드는 12자 입니다.")
        if String.isNullorEmpty(receiptID):
            raise BarocertException(-99999999, "접수아이디가 입력되지 않았습니다.")
        if False == receiptID.isdigit():
            raise BarocertException(-99999999, "접수아이디는 숫자만 입력할 수 있습니다.")
        if 32 != len(receiptID):
            raise BarocertException(-99999999, "접수아이디는 32자 입니다.")

        return self._httpget('/PASS/CMS/' + clientCode + '/' + receiptID)

    # 출금동의 검증
    def verifyCMS(self, clientCode, receiptID, cmsVerify):

        if String.isNullorEmpty(clientCode):
            raise BarocertException(-99999999, "이용기관코드가 입력되지 않았습니다.")
        if False == clientCode.isdigit():
            raise BarocertException(-99999999, "이용기관코드는 숫자만 입력할 수 있습니다.")
        if 12 != len(clientCode):
            raise BarocertException(-99999999, "이용기관코드는 12자 입니다.")
        if String.isNullorEmpty(receiptID):
            raise BarocertException(-99999999, "접수아이디가 입력되지 않았습니다.")
        if False == receiptID.isdigit():
            raise BarocertException(-99999999, "접수아이디는 숫자만 입력할 수 있습니다.")
        if 32 != len(receiptID):
            raise BarocertException(-99999999, "접수아이디는 32자 입니다.")
        if String.isNullorEmpty(cmsVerify):
            raise BarocertException(-99999999, "자동이체 출금동의 검증 요청 정보가 입력되지 않았습니다.")
        if String.isNullorEmpty(cmsVerify.receiverHP):
            raise BarocertException(-99999999, "수신자 휴대폰번호가 입력되지 않았습니다.")
        if String.isNullorEmpty(cmsVerify.receiverName):
            raise BarocertException(-99999999, "수신자 성명이 입력되지 않았습니다.")                
        
        postData = self._stringtify(cmsVerify)

        return self._httppost('/PASS/CMS/Verify/' + clientCode + '/' + receiptID, postData)
    
    # 간편로그인 요청
    def requestLogin(self, clientCode, login):

        if String.isNullorEmpty(clientCode):
            raise BarocertException(-99999999, "이용기관코드가 입력되지 않았습니다.")
        if False == clientCode.isdigit():
            raise BarocertException(-99999999, "이용기관코드는 숫자만 입력할 수 있습니다.")
        if 12 != len(clientCode):
            raise BarocertException(-99999999, "이용기관코드는 12자 입니다.")
        if String.isNullorEmpty(login):
            raise BarocertException(-99999999, "간편로그인 요청정보가 입력되지 않았습니다.")    
        if String.isNullorEmpty(login.receiverHP):
            raise BarocertException(-99999999, "수신자 휴대폰번호가 입력되지 않았습니다.")
        if String.isNullorEmpty(login.receiverName):
            raise BarocertException(-99999999, "수신자 성명이 입력되지 않았습니다.")
        if String.isNullorEmpty(login.reqTitle):
            raise BarocertException(-99999999, "인증요청 메시지 제목이 입력되지 않았습니다.")
        if String.isNullorEmpty(login.callCenterNum):
            raise BarocertException(-99999999, "고객센터 연락처가 입력되지 않았습니다.")            
        if String.isNullorEmpty(login.expireIn):
            raise BarocertException(-99999999, "만료시간이 입력되지 않았습니다.")
        if String.isNullorEmpty(login.token):
            raise BarocertException(-99999999, "토큰 원문이 입력되지 않았습니다.")
        
        postData = self._stringtify(login)

        return self._httppost('/PASS/Login/' + clientCode, postData)

    # 간편로그인 상태확인
    def getLoginStatus(self, clientCode, receiptID):

        if String.isNullorEmpty(clientCode):
            raise BarocertException(-99999999, "이용기관코드가 입력되지 않았습니다.")
        if False == clientCode.isdigit():
            raise BarocertException(-99999999, "이용기관코드는 숫자만 입력할 수 있습니다.")
        if 12 != len(clientCode):
            raise BarocertException(-99999999, "이용기관코드는 12자 입니다.")
        if String.isNullorEmpty(receiptID):
            raise BarocertException(-99999999, "접수아이디가 입력되지 않았습니다.")
        if False == receiptID.isdigit():
            raise BarocertException(-99999999, "접수아이디는 숫자만 입력할 수 있습니다.")
        if 32 != len(receiptID):
            raise BarocertException(-99999999, "접수아이디는 32자 입니다.")
        
        return self._httpget('/PASS/Login/' + clientCode + '/' + receiptID )
    
    # 간편로그인 검증
    def verifyLogin(self, clientCode, receiptID, loginVerify):

        if String.isNullorEmpty(clientCode):
            raise BarocertException(-99999999, "이용기관코드가 입력되지 않았습니다.")
        if False == clientCode.isdigit():
            raise BarocertException(-99999999, "이용기관코드는 숫자만 입력할 수 있습니다.")
        if 12 != len(clientCode):
            raise BarocertException(-99999999, "이용기관코드는 12자 입니다.")
        if String.isNullorEmpty(receiptID):
            raise BarocertException(-99999999, "접수아이디가 입력되지 않았습니다.")
        if False == receiptID.isdigit():
            raise BarocertException(-99999999, "접수아이디는 숫자만 입력할 수 있습니다.")
        if 32 != len(receiptID):
            raise BarocertException(-99999999, "접수아이디는 32자 입니다.")
        if String.isNullorEmpty(loginVerify):
            raise BarocertException(-99999999, "본인인증 검증 요청 정보가 입력되지 않았습니다.")
        if String.isNullorEmpty(loginVerify.receiverHP):
            raise BarocertException(-99999999, "수신자 휴대폰번호가 입력되지 않았습니다.")
        if String.isNullorEmpty(loginVerify.receiverName):
            raise BarocertException(-99999999, "수신자 성명이 입력되지 않았습니다.")

        postData = self._stringtify(loginVerify)

        return self._httppost('/PASS/Login/Verify/' + clientCode + '/' + receiptID, postData)

class PassCMS(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

class PassIdentity(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs
        
class PassLogin(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs        

class PassSign(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

class PassLoginVerify(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs        

class PassSignVerify(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

class PassCMSVerify(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

class PassIdentityVerify(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs
        