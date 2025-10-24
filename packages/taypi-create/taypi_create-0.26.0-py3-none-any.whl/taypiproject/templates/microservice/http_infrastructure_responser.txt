from app.components.http.domain.entities.response import Response

class APIResponser:

    @staticmethod
    def success(data: dict = None, message: str = 'Success', code: int = 200) -> dict:
        return data

    @staticmethod
    def valid(data: dict = None, message: str = 'Valid passed') -> Response:
        return Response(success=True, message=message, data=data, code=200)

    @staticmethod
    def error_response(data: dict = None, message: str = 'A Error occurred', code: int = 500) -> Response:
        return Response(success=False, message=message, data=data, code=code)

    @staticmethod
    def error_message(message: str | dict = 'A Error occurred', code: int = 400) -> Response:
        return Response(success=False, message=message, code=code)