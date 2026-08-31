import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List
from app.config import settings

class ResendEmailService:
    """
    Resend API Email Integration Service for Global Language Academy.
    Sends automated transactional emails (schedule change confirmations, ticket notifications, course quotes).
    """

    def __init__(self):
        self.api_url = "https://api.resend.com/emails"

    @property
    def is_configured(self) -> bool:
        return bool(settings.RESEND_API_KEY and len(settings.RESEND_API_KEY) > 5)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends an email using the Resend REST API or simulates sending if API key is not yet set.
        """
        if not to_email or "@" not in to_email:
            return {"success": False, "error": "Invalid email address"}

        payload = {
            "from": settings.RESEND_FROM_EMAIL,
            "to": [to_email.strip()],
            "subject": subject,
            "html": html_body
        }
        if text_body:
            payload["text"] = text_body

        if not self.is_configured:
            print(f"[ResendEmailService] Simulation: Email to '{to_email}' with subject '{subject}' queued (RESEND_API_KEY not configured).")
            return {
                "success": True,
                "simulated": True,
                "id": f"sim_resend_{to_email.split('@')[0]}",
                "to": to_email,
                "subject": subject
            }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.api_url,
                data=req_data,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                    "User-Agent": "GlobalLanguageAcademy/1.0"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                print(f"[ResendEmailService] ✅ Email sent to {to_email} via Resend. ID: {resp_data.get('id')}")
                return {
                    "success": True,
                    "simulated": False,
                    "id": resp_data.get("id"),
                    "to": to_email,
                    "subject": subject
                }
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            print(f"[ResendEmailService] HTTP Error {e.code} sending email to {to_email}: {err_msg}")
            return {"success": False, "error": f"HTTP {e.code}: {err_msg}"}
        except Exception as ex:
            print(f"[ResendEmailService] Error sending email to {to_email}: {ex}")
            return {"success": False, "error": str(ex)}

    def send_schedule_change_confirmation(
        self,
        to_email: str,
        new_schedule: str = "9:00 AM – 11:00 AM (Lunes a Jueves)",
        effective_mode: str = "Inmediato",
        ticket_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends an automated schedule change request confirmation to the student.
        """
        ticket_str = f"Ticket: {ticket_id}" if ticket_id else "Solicitud de Cambio de Horario"
        subject = f"Confirmación de Solicitud de Horario: {new_schedule} - Global Language Academy"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .card {{ max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); padding: 32px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }}
            .badge {{ display: inline-block; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 700; background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); text-transform: uppercase; }}
            h1 {{ font-size: 20px; font-weight: 800; color: #ffffff; margin-top: 16px; margin-bottom: 8px; }}
            p {{ font-size: 14px; line-height: 1.6; color: #cbd5e1; }}
            .details-box {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 16px; margin: 20px 0; }}
            .details-item {{ display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
            .details-item:last-child {{ border-bottom: none; }}
            .label {{ color: #94a3b8; }}
            .value {{ color: #f8fafc; font-weight: 600; }}
            .footer {{ text-align: center; margin-top: 24px; font-size: 12px; color: #64748b; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 16px; }}
          </style>
        </head>
        <body>
          <div class="card">
            <span class="badge">✓ Solicitud Registrada</span>
            <h1>¡Hola! Hemos recibido tu solicitud de horario</h1>
            <p>Tu solicitud para el cambio de horario al grupo de las <strong>{new_schedule}</strong> ha sido recibida y está siendo procesada por nuestro equipo de admisiones.</p>
            
            <div class="details-box">
              <div class="details-item">
                <span class="label">Horario Solicitado:</span>
                <span class="value">{new_schedule}</span>
              </div>
              <div class="details-item">
                <span class="label">Modalidad de Aplicación:</span>
                <span class="value">{effective_mode}</span>
              </div>
              <div class="details-item">
                <span class="label">Identificador de Gestión:</span>
                <span class="value">{ticket_id or 'GLA-REQ-SCHEDULE'}</span>
              </div>
              <div class="details-item">
                <span class="label">Tiempo de Respuesta:</span>
                <span class="value">Hoy mismo (vía este correo)</span>
              </div>
            </div>

            <p style="font-size: 13px; color: #94a3b8;">
              Un asesor académico validará la disponibilidad de cupo en la plataforma y te notificará por este medio la confirmación final de tu nuevo grupo.
            </p>

            <div class="footer">
              Global Language Academy • Asistencia y Admisiones Académicas<br>
              Este es un mensaje automático enviado a través de Resend.
            </div>
          </div>
        </body>
        </html>
        """

        text_body = (
            f"¡Hola!\n\n"
            f"Hemos recibido tu solicitud para el cambio de horario a: {new_schedule} ({effective_mode}).\n"
            f"Identificador: {ticket_id or 'GLA-REQ-SCHEDULE'}\n\n"
            f"Un asesor de admisiones validará el cupo disponible y te confirmará hoy mismo a este correo electrónico.\n\n"
            f"Global Language Academy."
        )

        return self.send_email(to_email=to_email, subject=subject, html_body=html_body, text_body=text_body)

email_service = ResendEmailService()
