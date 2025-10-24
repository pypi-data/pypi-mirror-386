# -- coding: utf-8 --
# Project: object_storage
# Created Date: 2025-05-01
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

from io import BytesIO
import logging
from typing import List, Optional, Dict
from minio import Minio
from minio.error import S3Error
from minio.commonconfig import Tags
from ..object_storage import ObjectStorage, StorageConfig
from ..type import DocFileObject

logger = logging.getLogger(__name__)

class MinioStorage(ObjectStorage):
    """MinIO存储实现"""
    
    def __init__(self, config: StorageConfig, auth_tenant_id: Optional[str] = None, auth_company_id: Optional[str] = None, doc_id: Optional[str] = None):
        """初始化MinIO客户端
        
        Args:
            config: 存储配置对象
            auth_tenant_id: 业务租户ID（可为空，后续操作可覆盖）
            auth_company_id: 业务公司ID（可为空，后续操作可覆盖）
            doc_id: 单据ID（可为空，后续操作可覆盖）
        """
        super().__init__(config, auth_tenant_id, auth_company_id, doc_id)
        
        # 处理endpoint格式
        endpoint = self._format_endpoint(config.endpoint)
        
        self.client = Minio(
            endpoint=endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.use_https  # 是否使用HTTPS
        )
        self.bucket_name = config.bucket_name
        
        # 确保bucket存在
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
            logger.info(f"create bucket: {self.bucket_name}")
        
    def _format_endpoint(self, endpoint: str) -> str:
        """格式化endpoint，确保符合MinIO要求
        
        Args:
            endpoint: 原始endpoint
            
        Returns:
            str: 格式化后的endpoint
            
        Raises:
            ValueError: endpoint格式不正确
        """
        # 移除协议前缀
        if endpoint.startswith(('http://', 'https://')):
            endpoint = endpoint.split('://', 1)[1]
            
        # 移除路径部分
        endpoint = endpoint.split('/', 1)[0]
        
        # 验证格式
        if '/' in endpoint:
            raise ValueError("MinIO endpoint can not contain path, format should be: host:port")
            
        return endpoint
    
    def upload_temp_file(self, object_key: str, data: bytes, tmppath: str = None) -> bool:
        """上传临时文件
        
        Args:
            object_key: 对象存储中的key
            tmppath: 临时文件路径, 如果为空，则使用默认临时目录
        """
        _path = f"{self.config.temp_dir}/{object_key}" if not tmppath else f"{tmppath.rstrip('/')}/{object_key}"
        return self.upload_file(_path, data)

    def download_temp_file(self, object_key: str, tmppath: str = None) -> bool:
        """下载临时文件
        
        Args:
            object_key: 对象存储中的key
            tmppath: 临时文件路径, 如果为空，则使用默认临时目录
        """
        _path = f"{self.config.temp_dir}/{object_key}" if not tmppath else f"{tmppath.rstrip('/')}/{object_key}"
        return self.download_file(_path)
        
    def upload_file(self, object_key: str, data: bytes) -> bool:
        """上传文件到MinIO
        
        Args:
            object_key: 对象存储中的key
            data: 文件数据
            
        Returns:
            bool: 是否上传成功
        """
        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                data=BytesIO(data),
                length=len(data)
            )
            logger.info(f"file upload success: {object_key}")
            return True
        except S3Error as e:
            logger.error(f"file upload failed: {str(e)}")
            return False
            
    def download_file(self, object_key: str) -> bytes:
        """从MinIO下载文件
        
        Args:
            object_key: 对象存储中的key
            
        Returns:
            bytes: 文件内容
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_key
            )
            return response.read()
        except S3Error as e:
            logger.error(f"file download failed: {str(e)}")
            return None
            
    def delete_file(self, object_key: str) -> bool:
        """删除MinIO中的文件
        
        Args:
            object_key: 对象存储中的key
            
        Returns:
            bool: 是否删除成功
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_key
            )
            logger.info(f"file delete success: {object_key}")
            return True
        except S3Error as e:
            logger.error(f"file delete failed: {str(e)}")
            return False
            
    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        """列出MinIO中的文件
        
        Args:
            prefix: 文件前缀过滤
            
        Returns:
            List[str]: 文件key列表
        """
        try:
            files = []
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix
            )
            for obj in objects:
                files.append(obj.object_name)
            return files
        except S3Error as e:
            logger.error(f"list files failed: {str(e)}")
            return [] 

    def _build_doc_path(self, filename: str, auth_tenant_id: Optional[str], auth_company_id: Optional[str], doc_id: Optional[str]) -> str:
        tenant_id = auth_tenant_id or self.auth_tenant_id
        company_id = auth_company_id or self.auth_company_id
        docid = doc_id or self.doc_id
        if not (tenant_id and company_id and docid):
            raise ValueError("auth_tenant_id、auth_company_id、doc_id 不能为空")
        return f"{tenant_id}/{company_id}/{docid}/{filename}"

    def upload_doc_file(self, 
                        filename: str, 
                        data: bytes, 
                        tags: Optional[Dict[str, str]] = None,
                        auth_tenant_id: Optional[str] = None, 
                        auth_company_id: Optional[str] = None, 
                        doc_id: Optional[str] = None) -> bool:
        """
        上传单据文件，自动拼接存储路径并打tag
        """
        try:
            object_key = self._build_doc_path(filename, auth_tenant_id, auth_company_id, doc_id)
            # 将tags转换为Tags对象
            tags_obj = Tags()
            if tags:
                for k, v in tags.items():
                    tags_obj[k] = v
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                data=BytesIO(data),
                length=len(data),
                tags=tags_obj
            )
            logger.info(f"doc file upload success: {object_key}")
            return True
        except S3Error as e:
            logger.error(f"doc file upload failed: {str(e)}")
            return False

    def download_doc_file(self, filename: str, auth_tenant_id: Optional[str] = None, auth_company_id: Optional[str] = None, doc_id: Optional[str] = None) -> bytes:
        try:
            object_key = self._build_doc_path(filename, auth_tenant_id, auth_company_id, doc_id)
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_key
            )
            return response.read()
        except S3Error as e:
            logger.error(f"doc file download failed: {str(e)}")
            return None

    def list_doc_files(self, auth_tenant_id: Optional[str] = None, auth_company_id: Optional[str] = None, doc_id: Optional[str] = None) -> List[DocFileObject]:
        try:
            tenant_id = auth_tenant_id or self.auth_tenant_id
            company_id = auth_company_id or self.auth_company_id
            docid = doc_id or self.doc_id
            if not (tenant_id and company_id and docid):
                raise ValueError("auth_tenant_id、auth_company_id、doc_id 不能为空")
            prefix = f"{tenant_id}/{company_id}/{docid}/"
            files: List[DocFileObject] = []
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix
            )
            for obj in objects:
                file_path = obj.object_name
                file_name = file_path.split("/")[-1]
                # 获取tag
                tags = {}
                try:
                    tag_res = self.client.get_object_tags(self.bucket_name, file_path)
                    tags = tag_res if tag_res else {}
                except Exception as tag_e:
                    logger.warning(f"get object tag failed: {file_path}, {str(tag_e)}")
                # 推断文件类型
                files.append(DocFileObject(
                    file_name=file_name,
                    tags=tags
                ))
            return files
        except S3Error as e:
            logger.error(f"list doc files failed: {str(e)}")
            return []

    def generate_presigned_url(self, object_key: str, method: str = "GET", expires_in: int = 3600, 
                              response_headers: Optional[Dict[str, str]] = None,
                              auth_tenant_id: Optional[str] = None, 
                              auth_company_id: Optional[str] = None, 
                              doc_id: Optional[str] = None) -> Optional[str]:
        """
        生成预签名URL
        
        Args:
            object_key: 对象存储中的key
            method: HTTP方法，支持 GET、PUT、POST、DELETE
            expires_in: 过期时间（秒），默认3600秒（1小时）
            response_headers: 响应头设置
            auth_tenant_id: 租户ID（可选，若不传则用实例属性）
            auth_company_id: 公司ID（可选，若不传则用实例属性）
            doc_id: 单据ID（可选，若不传则用实例属性）
            
        Returns:
            Optional[str]: 预签名URL，失败时返回None
        """
        try:
            # 验证参数
            if not object_key:
                raise ValueError("object_key 不能为空")
            
            if method.upper() not in ["GET", "PUT", "POST", "DELETE"]:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            if expires_in <= 0 or expires_in > 604800:  # 最大7天
                raise ValueError("过期时间必须在1秒到604800秒（7天）之间")
            
            # 生成预签名URL
            from datetime import timedelta
            
            if method.upper() == "GET":
                url = self.client.presigned_get_object(
                    bucket_name=self.bucket_name,
                    object_name=object_key,
                    expires=timedelta(seconds=expires_in),
                    response_headers=response_headers
                )
            elif method.upper() == "PUT":
                url = self.client.presigned_put_object(
                    bucket_name=self.bucket_name,
                    object_name=object_key,
                    expires=timedelta(seconds=expires_in)
                )
            elif method.upper() == "POST":
                url = self.client.presigned_post_policy(
                    bucket_name=self.bucket_name,
                    object_name=object_key,
                    expires=timedelta(seconds=expires_in)
                )
            elif method.upper() == "DELETE":
                url = self.client.presigned_delete_object(
                    bucket_name=self.bucket_name,
                    object_name=object_key,
                    expires=timedelta(seconds=expires_in)
                )
            
            logger.info(f"生成预签名URL成功: {object_key}, method: {method}")
            return url
            
        except S3Error as e:
            logger.error(f"生成预签名URL失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"生成预签名URL异常: {str(e)}")
            return None

    def generate_presigned_doc_url(self, filename: str, method: str = "GET", expires_in: int = 3600,
                                   response_headers: Optional[Dict[str, str]] = None,
                                   auth_tenant_id: Optional[str] = None, 
                                   auth_company_id: Optional[str] = None, 
                                   doc_id: Optional[str] = None) -> Optional[str]:
        """
        生成单据文件的预签名URL
        
        Args:
            filename: 文件名
            method: HTTP方法，支持 GET、PUT、POST、DELETE
            expires_in: 过期时间（秒），默认3600秒（1小时）
            response_headers: 响应头设置
            auth_tenant_id: 租户ID（可选，若不传则用实例属性）
            auth_company_id: 公司ID（可选，若不传则用实例属性）
            doc_id: 单据ID（可选，若不传则用实例属性）
            
        Returns:
            Optional[str]: 预签名URL，失败时返回None
        """
        try:
            # 构建单据文件路径
            object_key = self._build_doc_path(filename, auth_tenant_id, auth_company_id, doc_id)
            
            # 调用通用预签名URL生成方法
            return self.generate_presigned_url(
                object_key=object_key,
                method=method,
                expires_in=expires_in,
                response_headers=response_headers
            )
            
        except Exception as e:
            logger.error(f"生成单据文件预签名URL失败: {str(e)}")
            return None