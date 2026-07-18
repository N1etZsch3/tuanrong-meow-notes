import argparse

from sqlalchemy import select

from app.core.errors import APIError
from app.db.session import SessionLocal, configure_session
from app.modules.auth.models import User
from app.modules.files.models import FileAsset, FileAssetVariant  # noqa: F401
from app.modules.titles.service import seed_president


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grant the initial president title")
    parser.add_argument("--meow-no", required=True, help="Existing active member's meow number")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_session()
    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.student_no == args.meow_no,
                User.deleted_at.is_(None),
                User.status == "active",
            )
        )
        if user is None:
            print("未找到可用成员，未进行任何修改。")
            return 1
        try:
            seeded = seed_president(db, user=user)
        except APIError as exc:
            print(f"初始化失败：{exc.message}")
            return 1
        print(f"已将 {seeded.student_no} 初始化为会长。")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
