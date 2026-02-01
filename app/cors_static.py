from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

class CORSEnabledStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response: Response = await super().get_response(path, scope)

        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"

        return response
