import numpy as np

def parse_tpo(text: str):
    '''
    OpenAI API를 사용해 사용자의 텍스트 TPO를 파싱해 주요 키워드를 추출해 리스트로 반환
    
    args: text(str)
    return: List[]
    '''
    # 실제로는 openai api를 이용해 주요 키워드를 파싱할 예정
    return [w for w in text.split() if len(w) >= 2]

def clip_embed(text: str):
    '''
    query 텍스트의 clip embedding 생성
    
    args: text(str)
    return: np.array
    '''
    # 실제로는 clip 모델을 호출해 query embedding을 생성할 예정
    np.random.seed(abs(hash(text)) % (2**32))
    return np.random.rand(512)

def generate_reason(metadata: str, context: str):
    '''
    해당 아이템이 추천된 이유를 OpenAI API를 사용해 1-2문장으로 설명
    
    args:
    - context: persona + TPO
    - metadata: 추천된 아이템의 정보 (스타일, 이미지)
    '''
    return f"아이템의 {metadata}한 점이 {context}와 상황에서 잘 어울립니다."