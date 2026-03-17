from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorOut, VendorUpdate

router = APIRouter()


@router.post("", response_model=VendorOut, status_code=status.HTTP_201_CREATED)
def create_vendor(payload: VendorCreate, db: Session = Depends(get_db)):
    try:
        vendor = Vendor(**payload.model_dump())
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return vendor
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Vendor with same name/email already exists") from e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create vendor") from e


@router.get("", response_model=list[VendorOut])
def list_vendors(db: Session = Depends(get_db)):
    try:
        return list(db.scalars(select(Vendor).order_by(Vendor.id)).all())
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch vendors") from e


@router.get("/{vendor_id}", response_model=VendorOut)
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
    try:
        vendor = db.get(Vendor, vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return vendor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch vendor") from e


@router.put("/{vendor_id}", response_model=VendorOut)
def update_vendor(vendor_id: int, payload: VendorUpdate, db: Session = Depends(get_db)):
    try:
        vendor = db.get(Vendor, vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(vendor, k, v)

        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return vendor
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Vendor with same name/email already exists") from e
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update vendor") from e


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(vendor_id: int, db: Session = Depends(get_db)):
    try:
        vendor = db.get(Vendor, vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        db.delete(vendor)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete vendor") from e
