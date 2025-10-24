# -*- coding: utf-8 -*-

from .base import BaseService, BarocertException
from .util import String

class KakaocertService(BaseService):

    def __init__(self, LinkID, SecretKey, timeOut=15):
        """ 생성자.
            args
                LinkID : 링크허브에서 발급받은 LinkID
                SecretKey : 링크허브에서 발급받은 SecretKey
        """
        super(self.__class__, self).__init__(LinkID, SecretKey)
        self._addScope("401")
        self._addScope("402")
        self._addScope("403")
        self._addScope("404")
        self._addScope("405")
            
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
        if String.isNullorEmpty(identity.receiverBirthday):
            raise BarocertException(-99999999, "생년월일이 입력되지 않았습니다.")
        if String.isNullorEmpty(identity.reqTitle):
            raise BarocertException(-99999999, "인증요청 메시지 제목이 입력되지 않았습니다.")
        if String.isNullorEmpty(identity.expireIn):
            raise BarocertException(-99999999, "만료시간이 입력되지 않았습니다.")
        if String.isNullorEmpty(identity.token):
            raise BarocertException(-99999999, "토큰 원문이 입력되지 않았습니다.")
        
        postData = self._stringtify(identity)

        return self._httppost('/KAKAO/Identity/' + clientCode, postData)

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
        

        return self._httpget('/KAKAO/Identity/' + clientCode + '/' + receiptID )
    
    # 본인인증 검증
    def verifyIdentity(self, clientCode, receiptID):

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

        return self._httppost('/KAKAO/Identity/Verify/' + clientCode + '/' + receiptID )

    # 전자서명 요청(단건)
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
        if String.isNullorEmpty(sign.receiverBirthday):
            raise BarocertException(-99999999, "생년월일이 입력되지 않았습니다.")
        if String.isNullorEmpty(sign.signTitle) and String.isNullorEmpty(sign.reqTitle):
            raise BarocertException(-99999999, "인증요청 메시지 제목이 입력되지 않았습니다.")
        if String.isNullorEmpty(sign.expireIn):
            raise BarocertException(-99999999, "만료시간이 입력되지 않았습니다.")
        if String.isNullorEmpty(sign.token):
            raise BarocertException(-99999999, "토큰 원문이 입력되지 않았습니다.")
        if String.isNullorEmpty(sign.tokenType):
            raise BarocertException(-99999999, "원문 유형이 입력되지 않았습니다.")
        
        postData = self._stringtify(sign)

        return self._httppost('/KAKAO/Sign/' + clientCode, postData)

    # 전자서명 상태확인(단건)
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

        return self._httpget('/KAKAO/Sign/' + clientCode + '/' + receiptID)

    # 전자서명 검증(단건)
    def verifySign(self, clientCode, receiptID):

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

        return self._httppost('/KAKAO/Sign/Verify/' + clientCode + '/' + receiptID)
    
    # 전자서명 요청(복수)
    def requestMultiSign(self, clientCode, multiSign):

        if String.isNullorEmpty(clientCode):
            raise BarocertException(-99999999, "이용기관코드가 입력되지 않았습니다.")
        if False == clientCode.isdigit():
            raise BarocertException(-99999999, "이용기관코드는 숫자만 입력할 수 있습니다.")
        if 12 != len(clientCode):
            raise BarocertException(-99999999, "이용기관코드는 12자 입니다.")
        if String.isNullorEmpty(multiSign):
            raise BarocertException(-99999999, "전자서명 요청정보가 입력되지 않았습니다.")
        if String.isNullorEmpty(multiSign.receiverHP):
            raise BarocertException(-99999999, "수신자 휴대폰번호가 입력되지 않았습니다.")
        if String.isNullorEmpty(multiSign.receiverName):
            raise BarocertException(-99999999, "수신자 성명이 입력되지 않았습니다.")
        if String.isNullorEmpty(multiSign.receiverBirthday):
            raise BarocertException(-99999999, "생년월일이 입력되지 않았습니다.")
        if String.isNullorEmpty(multiSign.reqTitle):
            raise BarocertException(-99999999, "인증요청 메시지 제목이 입력되지 않았습니다.")
        if String.isNullorEmpty(multiSign.expireIn):
            raise BarocertException(-99999999, "만료시간이 입력되지 않았습니다.")
        if self._isNullorEmptyTitle(multiSign.tokens):
            raise BarocertException(-99999999, "인증요청 메시지 제목이 입력되지 않았습니다.")
        if self._isNullorEmptyToken(multiSign.tokens):
            raise BarocertException(-99999999, "토큰 원문이 입력되지 않았습니다.")
        if String.isNullorEmpty(multiSign.tokenType):
            raise BarocertException(-99999999, "원문 유형이 입력되지 않았습니다.")

        postData = self._stringtify(multiSign)

        return self._httppost('/KAKAO/MultiSign/' + clientCode, postData)

    # 전자서명 상태확인(복수)	
    def getMultiSignStatus(self, clientCode, receiptID):

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

        return self._httpget('/KAKAO/MultiSign/' + clientCode + '/' + receiptID)


    # 전자서명 검증(복수)
    def verifyMultiSign(self, clientCode, receiptID):

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
        
        return self._httppost('/KAKAO/MultiSign/Verify/' + clientCode + '/' + receiptID)

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
        if String.isNullorEmpty(cms.receiverBirthday):
            raise BarocertException(-99999999, "생년월일이 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.reqTitle):
            raise BarocertException(-99999999, "인증요청 메시지 제목이 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.expireIn):
            raise BarocertException(-99999999, "만료시간이 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.requestCorp):
            raise BarocertException(-99999999, "청구기관명이 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.bankName):
            raise BarocertException(-99999999, "은행명이 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.bankAccountNum):
            raise BarocertException(-99999999, "계좌번호가 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.bankAccountName):
            raise BarocertException(-99999999, "예금주명이 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.bankAccountBirthday):
            raise BarocertException(-99999999, "예금주 생년월일이 입력되지 않았습니다.")
        if String.isNullorEmpty(cms.bankServiceType):
            raise BarocertException(-99999999, "출금 유형이 입력되지 않았습니다.")

        postData = self._stringtify(cms)

        return self._httppost('/KAKAO/CMS/' + clientCode, postData)

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

        return self._httpget('/KAKAO/CMS/' + clientCode + '/' + receiptID)

    # 출금동의 검증
    def verifyCMS(self, clientCode, receiptID):

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
        
        return self._httppost('/KAKAO/CMS/Verify/' + clientCode + '/' + receiptID)
    
    # 간편로그인 검증
    def verifyLogin(self, clientCode, txID):

        if String.isNullorEmpty(clientCode):
            raise BarocertException(-99999999, "이용기관코드가 입력되지 않았습니다.")
        if False == clientCode.isdigit():
            raise BarocertException(-99999999, "이용기관코드는 숫자만 입력할 수 있습니다.")
        if 12 != len(clientCode):
            raise BarocertException(-99999999, "이용기관코드는 12자 입니다.")
        if String.isNullorEmpty(txID):
            raise BarocertException(-99999999, "트랜잭션 아이디가 입력되지 않았습니다.")
        
        return self._httppost('/KAKAO/Login/Verify/' + clientCode + '/' + txID)

    def _isNullorEmptyTitle(self, multiSignTokens):
        if multiSignTokens == None or multiSignTokens == "":
            return True
        if len(multiSignTokens) == 0:
            return True
        for multiSignToken in multiSignTokens:
            if (String.isNullorEmpty(multiSignToken.signTitle) and String.isNullorEmpty(multiSignToken.reqTitle)):
                return True
        return False
    
    def _isNullorEmptyToken(self, multiSignTokens):
        if multiSignTokens == None or multiSignTokens == "":
            return True
        if len(multiSignTokens) == 0:
            return True
        for multiSignToken in multiSignTokens:
            if String.isNullorEmpty(multiSignToken.token):
                return True
        return False


class KakaoCMS(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

class KakaoIdentity(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs
        
class KakaoSign(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

class KakaoMultiSign(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

class KakaoMultiSignTokens(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs
