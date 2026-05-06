from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import UserInfo, SysCommand, WebCommand, Contact

router = APIRouter()


class InfoOut(BaseModel):
    name: str | None = None
    designation: str | None = None
    mobileno: str | None = None
    email: str | None = None
    city: str | None = None
    model_config = {"from_attributes": True}


class InfoIn(BaseModel):
    name: str
    designation: str
    mobileno: str
    email: str
    city: str


@router.get("/api/settings/info", response_model=InfoOut)
def get_info(db: Session = Depends(get_db)):
    row = db.query(UserInfo).first()
    return row or InfoOut()


@router.post("/api/settings/info", response_model=InfoOut)
def save_info(body: InfoIn, db: Session = Depends(get_db)):
    row = db.query(UserInfo).first()
    if row:
        for k, v in body.model_dump().items():
            setattr(row, k, v)
    else:
        row = UserInfo(**body.model_dump())
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


class CmdOut(BaseModel):
    id: int
    name: str
    path: str | None = None
    url: str | None = None
    model_config = {"from_attributes": True}


@router.get("/api/settings/syscommands", response_model=list[CmdOut])
def list_syscommands(db: Session = Depends(get_db)):
    return db.query(SysCommand).all()


@router.post("/api/settings/syscommands", response_model=CmdOut, status_code=201)
def add_syscommand(body: dict, db: Session = Depends(get_db)):
    cmd = SysCommand(name=body["name"], path=body["path"])
    db.add(cmd)
    db.commit()
    db.refresh(cmd)
    return cmd


@router.delete("/api/settings/syscommands/{cmd_id}", status_code=204)
def delete_syscommand(cmd_id: int, db: Session = Depends(get_db)):
    cmd = db.query(SysCommand).filter_by(id=cmd_id).first()
    if not cmd:
        raise HTTPException(404)
    db.delete(cmd)
    db.commit()


@router.get("/api/settings/webcommands", response_model=list[CmdOut])
def list_webcommands(db: Session = Depends(get_db)):
    return db.query(WebCommand).all()


@router.post("/api/settings/webcommands", response_model=CmdOut, status_code=201)
def add_webcommand(body: dict, db: Session = Depends(get_db)):
    cmd = WebCommand(name=body["name"], url=body["url"])
    db.add(cmd)
    db.commit()
    db.refresh(cmd)
    return cmd


@router.delete("/api/settings/webcommands/{cmd_id}", status_code=204)
def delete_webcommand(cmd_id: int, db: Session = Depends(get_db)):
    cmd = db.query(WebCommand).filter_by(id=cmd_id).first()
    if not cmd:
        raise HTTPException(404)
    db.delete(cmd)
    db.commit()


class ContactOut(BaseModel):
    id: int
    name: str
    mobile_no: str
    email: str | None = None
    address: str | None = None
    model_config = {"from_attributes": True}


class ContactIn(BaseModel):
    name: str
    mobile_no: str
    email: str = ""
    address: str = ""


@router.get("/api/settings/contacts", response_model=list[ContactOut])
def list_contacts(db: Session = Depends(get_db)):
    return db.query(Contact).all()


@router.post("/api/settings/contacts", response_model=ContactOut, status_code=201)
def add_contact(body: ContactIn, db: Session = Depends(get_db)):
    c = Contact(**body.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/api/settings/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    c = db.query(Contact).filter_by(id=contact_id).first()
    if not c:
        raise HTTPException(404)
    db.delete(c)
    db.commit()
