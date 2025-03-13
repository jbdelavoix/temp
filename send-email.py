import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE

# Définir les informations d'identification de l'expéditeur et du destinataire
FROM = "adresseemail@expediteur.com"
PASSWORD = "motdepasse"
TO = ["adresseemail@destinataire.com"]

# Créer un objet MIMEMultipart et ajouter les détails de l'e-mail
msg = MIMEMultipart()
msg["From"] = FROM
msg["To"] = COMMASPACE.join(TO)
msg["Subject"] = "Objet du mail"

# Ajouter le corps du mail
body = "Bonjour,\n\nVoici la pièce jointe que vous avez demandée.\n\nCordialement,\nExpéditeur"
msg.attach(MIMEText(body, "plain"))

# Ouvrir le fichier à joindre
filename = "chemin/vers/la/piece/jointe"
attachment = open(filename, "rb")

# Ajouter la pièce jointe au message
part = MIMEBase("application", "octet-stream")
part.set_payload((attachment).read())
encoders.encode_base64(part)
part.add_header("Content-Disposition", "piece; filename= %s" % filename)

msg.attach(part)

# Envoyer l'e-mail en utilisant SMTP
server = smtplib.SMTP("smtp.gmail.com", 587)  # Remplacer par votre serveur SMTP
server.starttls()
server.login(FROM, PASSWORD)
text = msg.as_string()
server.sendmail(FROM, TO, text)
server.quit()

print("L'e-mail a été envoyé avec succès!")
