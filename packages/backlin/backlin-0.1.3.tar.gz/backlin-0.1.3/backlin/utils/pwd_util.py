import bcrypt
import hashlib

# 使用纯 bcrypt，通过 SHA256 预处理来支持任意长度密码
class PwdUtil:
    """
    密码工具类 - 使用 bcrypt + SHA256 预处理来支持任意长度密码
    """

    @classmethod
    def _prepare_password(cls, password: str) -> bytes:
        """
        预处理密码：对超长密码先做 SHA256，确保不超过 72 字节
        """
        if isinstance(password, str):
            password_bytes = password.encode('utf-8')
        else:
            password_bytes = password

        # 如果密码超过 72 字节，先做 SHA256
        if len(password_bytes) > 72:
            return hashlib.sha256(password_bytes).hexdigest().encode('utf-8')
        return password_bytes

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """
        工具方法：校验当前输入的密码与数据库存储的密码是否一致
        :param plain_password: 当前输入的密码
        :param hashed_password: 数据库存储的密码
        :return: 校验结果
        """
        try:
            prepared_password = cls._prepare_password(plain_password)
            hashed_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
            return bcrypt.checkpw(prepared_password, hashed_bytes)
        except Exception:
            return False

    @classmethod
    def get_password_hash(cls, input_password: str) -> str:
        """
        工具方法：对当前输入的密码进行加密
        :param input_password: 输入的密码
        :return: 加密成功的密码
        """
        prepared_password = cls._prepare_password(input_password)
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(prepared_password, salt)
        return hashed.decode('utf-8')

    @classmethod
    def needs_update(cls, hashed_password: str) -> bool:
        """
        判断给定哈希是否需要升级
        对于 bcrypt，我们认为所有有效的哈希都不需要更新
        """
        try:
            # 简单检查是否是有效的 bcrypt 哈希
            return not (hashed_password.startswith('$2a$') or
                       hashed_password.startswith('$2b$') or
                       hashed_password.startswith('$2y$'))
        except Exception:
            return True
