from django.shortcuts import render
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import ask_chatbot


class ChatbotAPIView(APIView):
    def post(self, request):
        if not settings.OPENAI_API_KEY:
            return Response(
                {"error": "OPENAI_API_KEY is not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        message = request.data.get("message", "").strip()

        if not message:
            return Response(
                {"error": "Message is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(message) > 1000:
            return Response(
                {"error": "Message is too long."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            reply = ask_chatbot(request.user, message)
            return Response({"reply": reply}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {
                    "error": "Could not generate chatbot reply.",
                    "detail": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )