from fastapi import APIRouter, HTTPException, Query
import json
from database import get_pool
from mail import send_email_via_smtp, update_sent_mail

router = APIRouter(
    prefix="/api",
    tags=["Api"]
)

async def get_supplier_contact(username: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            try:
                query = "SELECT fn_get_supplier_contact($1) AS data;"
                row = await conn.fetchrow(query, username)

                if not row or not row["data"]:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No se encontró información para el usuario '{username}'."
                    )
                data = json.loads(row["data"])

                return data

            except Exception as e:
                raise HTTPException(status_code=404, detail=f"Error al obtener datos del proveedor: {e}")


@router.post("/contact",
             summary="Contactar vendedor",
             description="Envía un correo predefinido al proveedor asociado al usuario recibido.",
             responses={
                 200:{
                        "description": "Ejecución exitosa",
                        "content": {
                            "application/json": {
                                "example": {"message": "Correo enviado correctamente. El proveedor se pondrá en contacto a la brevedad al correo john.doe@ecom.com.uy"
                                }
                            }
                        },
                    },
                404: {
                        "description": "Error interno del servidor",
                        "content": {
                            "application/json": {
                                "example": {
                                     "detail": "Error al obtener datos del proveedor: 404: No se encontró información para el usuario 'johnDoe123'."
                                }
                            }
                        },
                    }
                }
            )

async def notify_supplier(username: str = Query(...,example="johnDoe123")):
    try:
        supplier_contact = await get_supplier_contact(username)

        if supplier_contact.get("hasSentMail", False):
            return {
                "message": f"El usuario {supplier_contact['userFullName']} ya envió un correo. "
                           "Debe esperar la respuesta del proveedor."
            }

        subject = "Solicitud de contacto"
        body = (
            f"Estimado proveedor:\n\n"
            f"Le informamos que se ha realizado una solicitud de contacto "
            f"asociada al usuario {supplier_contact['userFullName']} (ID: {supplier_contact['userId']}) "
            f"de la empresa {supplier_contact['companyName']} (ID: {supplier_contact['companyId']})."
            f"Puede comunicarse con el usuario al correo {supplier_contact['userMail']}.\n\n"
            "Atentamente,\n"
            "El equipo de soporte."
        )

        send_email_via_smtp(subject, body, supplier_contact['supplierMail'])
        await update_sent_mail(user=username, status=True)
        return {"message": f"Correo enviado correctamente. El proveedor se pondrá en contacto a la brevedad al correo {supplier_contact['userMail']}"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
