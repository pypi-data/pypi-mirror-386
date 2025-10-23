from sqlalchemy.orm import Session
from backlin.module_admin.entity.do.post_do import SysPost
from backlin.module_admin.entity.vo.post_vo import PostModel
from backlin.utils.time_format_util import list_format_datetime


class PostDao:
    """
    岗位管理模块数据库操作层
    """

    @classmethod
    def get_post_by_id(cls, db: Session, post_id: int):
        """
        根据岗位id获取在用岗位详细信息
        :param db: orm对象
        :param post_id: 岗位id
        :return: 在用岗位信息对象
        """
        post_info = db.query(SysPost) \
            .filter(SysPost.post_id == post_id,
                    SysPost.status == 0) \
            .first()

        return post_info

    @classmethod
    def get_post_detail_by_id(cls, db: Session, post_id: int):
        """
        根据岗位id获取岗位详细信息
        :param db: orm对象
        :param post_id: 岗位id
        :return: 岗位信息对象
        """
        post_info = db.query(SysPost) \
            .filter(SysPost.post_id == post_id) \
            .first()

        return post_info

    @classmethod
    def get_post_detail_by_info(cls, db: Session, post: PostModel):
        """
        根据岗位参数获取岗位信息
        :param db: orm对象
        :param post: 岗位参数对象
        :return: 岗位信息对象
        """
        post_info = db.query(SysPost) \
            .filter(SysPost.post_name == post.post_name if post.post_name else True,
                    SysPost.post_code == post.post_code if post.post_code else True,
                    SysPost.post_sort == post.post_sort if post.post_sort else True) \
            .first()

        return post_info

    @classmethod
    def get_post_select_option_dao(cls, db: Session):
        """
        获取所有在用岗位信息
        :param db: orm对象
        :return: 在用岗位信息列表
        """
        post_info = db.query(SysPost) \
            .filter(SysPost.status == 0) \
            .all()

        return post_info

    @classmethod
    def get_post_list(cls, db: Session, query_object: PostModel):
        """
        根据查询参数获取岗位列表信息
        :param db: orm对象
        :param query_object: 查询参数对象
        :return: 岗位列表信息对象
        """
        conditions = []
        if query_object.post_code:
            conditions.append(SysPost.post_code.like(f'%{query_object.post_code}%'))
        if query_object.post_name:
            conditions.append(SysPost.post_name.like(f'%{query_object.post_name}%'))
        if query_object.status:
            conditions.append(SysPost.status == query_object.status)
        q = db.query(SysPost)
        if len(conditions) > 0:
            q = q.filter(*tuple(conditions))
        post_list = q.order_by(SysPost.post_sort).distinct().all()

        return list_format_datetime(post_list)

    @classmethod
    def add_post_dao(cls, db: Session, post: PostModel):
        """
        新增岗位数据库操作
        :param db: orm对象
        :param post: 岗位对象
        :return:
        """
        db_post = SysPost(**post.dict())
        db.add(db_post)
        db.flush()

        return db_post

    @classmethod
    def edit_post_dao(cls, db: Session, post: dict):
        """
        编辑岗位数据库操作
        :param db: orm对象
        :param post: 需要更新的岗位字典
        :return:
        """
        db.query(SysPost) \
            .filter(SysPost.post_id == post.get('post_id')) \
            .update(post)

    @classmethod
    def delete_post_dao(cls, db: Session, post: PostModel):
        """
        删除岗位数据库操作
        :param db: orm对象
        :param post: 岗位对象
        :return:
        """
        db.query(SysPost) \
            .filter(SysPost.post_id == post.post_id) \
            .delete()
