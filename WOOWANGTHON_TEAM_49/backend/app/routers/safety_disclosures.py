from fastapi import APIRouter, Depends, Query, Request

from app.errors import ApiError, ok
from app.outputs import API, ErrorData, SafetyDisclosureSearchDTO
from app.security import current_user

router = APIRouter(tags=['Safety Disclosures'])


@router.get('/safety-disclosures', response_model=API[SafetyDisclosureSearchDTO],
            responses={503: {'model': API[ErrorData],
                             'description': 'Packaged official disclosure dataset unavailable'}})
def search_safety_disclosures(request: Request, q: str = Query(min_length=1, max_length=200),
                             address: str | None = Query(default=None, max_length=1000),
                             page: int = Query(1, ge=1), size: int = Query(5, ge=1, le=20),
                             user=Depends(current_user)):
    if not q.strip():
        raise ApiError(422, 'INVALID_SAFETY_DISCLOSURE_QUERY', '검색할 사업장 이름을 입력해 주세요.')
    directory = request.app.state.safety_disclosures
    if directory is None:
        raise ApiError(503, 'SAFETY_DISCLOSURE_DATASET_UNAVAILABLE',
                       '산업재해 공표 자료를 불러올 수 없습니다. 잠시 후 다시 시도해 주세요.')
    return ok(directory.search(q, address, page, size))
