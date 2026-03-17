from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services.ai_description import generate_product_description

router = APIRouter()


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    try:
        product = Product(**payload.model_dump())
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product with same SKU already exists") from e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create product") from e


@router.get("", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    try:
        return list(db.scalars(select(Product).order_by(Product.id)).all())
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch products") from e


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch product") from e


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    try:
        product = db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(product, k, v)

        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product with same SKU already exists") from e
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update product") from e


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        db.delete(product)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete product") from e


@router.post("/{product_id}/generate-description")
async def generate_description(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        description = await generate_product_description(product.name)
        return {"product_id": product.id, "product_name": product.name, "description": description}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate description") from e
