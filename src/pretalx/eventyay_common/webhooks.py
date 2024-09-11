import json

import jwt
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from pretalx.eventyay_common.tasks import (
    process_create_organiser_webhook,
    process_create_team_webhook,
)
from pretalx.person.models import User


@csrf_exempt
def organiser_webhook(request):
    permission_required = ("orga.change_organiser_settings",)
    if request.method == "POST":
        # Get the Authorization header
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            # Extract the token from the header
            token = auth_header.split(" ")[1]

            try:
                # Decode and validate the JWT token
                decoded_data = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=["HS256"]
                )

                # Check if user from jwt has permission to change organiser
                user = User.objects.get(email=decoded_data["email"])
                if not user.has_perms(permission_required, None):
                    return JsonResponse(
                        {"status": "User does not have permission to change organiser"},
                        status=403,
                    )
                # Check if user from jwt has permission to create organiser
                # Now process the webhook as usual
                organiser_data = json.loads(request.body)
                process_create_organiser_webhook.delay(organiser_data)

                return JsonResponse({"status": "success"}, status=200)

            except jwt.ExpiredSignatureError:
                return JsonResponse({"status": "Token has expired"}, status=401)
            except jwt.InvalidTokenError:
                return JsonResponse({"status": "Invalid token"}, status=401)
        else:
            return JsonResponse(
                {"status": "Authorization header missing or invalid"}, status=403
            )

    return JsonResponse({"status": "Invalid method"}, status=405)


@csrf_exempt
def team_webhook(request):
    permission_required = ("orga.change_teams",)
    if request.method == "POST":
        # Get the Authorization header
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            # Extract the token from the header
            token = auth_header.split(" ")[1]

            try:
                # Decode and validate the JWT token
                decoded_data = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=["HS256"]
                )

                # Check if user from jwt has permission to change team
                user = User.objects.get(email=decoded_data["email"])
                if not user.has_perms(permission_required, None):
                    return JsonResponse(
                        {"status": "User does not have permission to change team"},
                        status=403,
                    )
                # Now process the webhook as usual
                organiser_data = json.loads(request.body)
                process_create_team_webhook.delay(organiser_data)

                return JsonResponse({"status": "success"}, status=200)

            except jwt.ExpiredSignatureError:
                return JsonResponse({"status": "Token has expired"}, status=401)
            except jwt.InvalidTokenError:
                return JsonResponse({"status": "Invalid token"}, status=401)
        else:
            return JsonResponse(
                {"status": "Authorization header missing or invalid"}, status=403
            )

    return JsonResponse({"status": "Invalid method"}, status=405)
