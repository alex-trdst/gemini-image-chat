"""
Shopify Files Upload Module

Shopify Admin API를 사용하여 이미지 파일 업로드
Client Credentials (OAuth) 방식 인증
"""

import base64
import httpx
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class UploadedFile:
    """업로드된 파일 정보"""
    url: str
    alt: Optional[str] = None
    file_id: Optional[str] = None


class ShopifyFilesService:
    """Shopify Files API 서비스 (Client Credentials 인증)"""

    def __init__(self, store_url: str, client_id: str, client_secret: str):
        """
        Args:
            store_url: Shopify 스토어 URL (예: https://mystore.myshopify.com)
            client_id: Shopify 앱 Client ID
            client_secret: Shopify 앱 Client Secret
        """
        self.store_url = store_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.graphql_url = f"{self.store_url}/admin/api/2024-01/graphql.json"
        self._access_token: Optional[str] = None

    async def _get_access_token(self) -> str:
        """Client Credentials로 액세스 토큰 발급"""
        if self._access_token:
            return self._access_token

        token_url = f"{self.store_url}/admin/oauth/access_token"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                logger.error(f"Shopify 토큰 발급 실패: {response.status_code} - {response.text}")
                raise ValueError(f"Shopify 토큰 발급 실패: {response.status_code}")

            data = response.json()
            self._access_token = data.get("access_token")

            if not self._access_token:
                logger.error(f"Shopify 토큰 응답에 access_token 없음: {data}")
                raise ValueError("Shopify 토큰 응답에 access_token이 없습니다.")

            logger.info("Shopify 액세스 토큰 발급 성공")
            return self._access_token

    async def _get_headers(self) -> dict:
        """인증 헤더 반환"""
        access_token = await self._get_access_token()
        return {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": access_token,
        }

    async def upload_image(
        self,
        image_data: bytes,
        filename: str,
        mime_type: str = "image/png",
        alt: Optional[str] = None,
    ) -> UploadedFile:
        """
        이미지를 Shopify Files에 업로드

        Args:
            image_data: 이미지 바이너리 데이터
            filename: 파일명 (예: marketing-image-123.png)
            mime_type: MIME 타입
            alt: 이미지 대체 텍스트

        Returns:
            UploadedFile: 업로드된 파일 정보 (URL 포함)
        """
        headers = await self._get_headers()

        async with httpx.AsyncClient() as client:
            # Step 1: stagedUploadsCreate로 업로드 URL 받기
            staged_mutation = """
            mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
              stagedUploadsCreate(input: $input) {
                stagedTargets {
                  url
                  resourceUrl
                  parameters {
                    name
                    value
                  }
                }
                userErrors {
                  field
                  message
                }
              }
            }
            """

            staged_response = await client.post(
                self.graphql_url,
                headers=headers,
                json={
                    "query": staged_mutation,
                    "variables": {
                        "input": [{
                            "filename": filename,
                            "mimeType": mime_type,
                            "resource": "FILE",
                            "httpMethod": "POST",
                        }]
                    }
                },
                timeout=30.0,
            )
            staged_data = staged_response.json()

            if "errors" in staged_data:
                raise ValueError(f"Shopify API 오류: {staged_data['errors']}")

            staged_result = staged_data["data"]["stagedUploadsCreate"]
            if staged_result["userErrors"]:
                raise ValueError(f"업로드 준비 실패: {staged_result['userErrors']}")

            target = staged_result["stagedTargets"][0]
            upload_url = target["url"]
            resource_url = target["resourceUrl"]
            parameters = {p["name"]: p["value"] for p in target["parameters"]}

            # Step 2: 서명된 URL로 파일 업로드
            form_data = dict(parameters)
            files = {"file": (filename, image_data, mime_type)}

            upload_response = await client.post(
                upload_url,
                data=form_data,
                files=files,
                timeout=60.0,
            )

            if upload_response.status_code not in (200, 201, 204):
                raise ValueError(f"파일 업로드 실패: {upload_response.status_code}")

            # Step 3: fileCreate로 파일 레코드 생성
            file_mutation = """
            mutation fileCreate($files: [FileCreateInput!]!) {
              fileCreate(files: $files) {
                files {
                  id
                  alt
                  ... on MediaImage {
                    image {
                      url
                    }
                  }
                }
                userErrors {
                  field
                  message
                }
              }
            }
            """

            file_response = await client.post(
                self.graphql_url,
                headers=headers,
                json={
                    "query": file_mutation,
                    "variables": {
                        "files": [{
                            "alt": alt or filename,
                            "contentType": "IMAGE",
                            "originalSource": resource_url,
                        }]
                    }
                },
                timeout=30.0,
            )
            file_data = file_response.json()

            if "errors" in file_data:
                raise ValueError(f"파일 생성 오류: {file_data['errors']}")

            file_result = file_data["data"]["fileCreate"]
            if file_result["userErrors"]:
                raise ValueError(f"파일 생성 실패: {file_result['userErrors']}")

            # 파일 URL 가져오기 (처리 중일 수 있으므로 resourceUrl 사용)
            created_file = file_result["files"][0] if file_result["files"] else None

            if created_file and "image" in created_file and created_file["image"]:
                final_url = created_file["image"]["url"]
            else:
                # 이미지 처리 중이면 resourceUrl 사용
                final_url = resource_url

            return UploadedFile(
                url=final_url,
                alt=alt,
                file_id=created_file["id"] if created_file else None,
            )

    async def upload_base64_image(
        self,
        base64_data: str,
        filename: str,
        mime_type: str = "image/png",
        alt: Optional[str] = None,
    ) -> UploadedFile:
        """
        Base64 인코딩된 이미지를 Shopify Files에 업로드

        Args:
            base64_data: Base64 인코딩된 이미지 데이터
            filename: 파일명
            mime_type: MIME 타입
            alt: 이미지 대체 텍스트

        Returns:
            UploadedFile: 업로드된 파일 정보
        """
        image_data = base64.b64decode(base64_data)
        return await self.upload_image(image_data, filename, mime_type, alt)
