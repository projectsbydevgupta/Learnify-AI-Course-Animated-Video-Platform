from sqlalchemy.orm import Session
import models
import schemas

def create_user(db: Session, user: schemas.UserCreate):
    existing_user = db.query(models.User).filter(models.User.clerk_id == user.clerk_id).first()
    if existing_user:
        return existing_user
    db_user = models.User(clerk_id=user.clerk_id, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_job(db: Session, job: schemas.JobCreate):
    db_job = models.GenerationJob(
        user_id=job.user_id,
        job_type=job.job_type,
        status="pending",
        progress_percent=0,
        current_stage="initialized"
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def get_job(db: Session, job_id: str):
    return db.query(models.GenerationJob).filter(models.GenerationJob.id == job_id).first()