"""Vue API : consultation et mise a jour du profil utilisateur."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Profile


def serialize_profile(profile):
    """Profile -> dict, format attendu par le frontend."""
    return {
        "diet": profile.diet,
        "allergies": profile.allergies,
        "skill_level": profile.skill_level,
        "time_available_minutes": profile.time_available_minutes,
    }


class ProfileView(APIView):
    """GET /api/profile/ et PATCH /api/profile/."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(serialize_profile(request.user.profile))

    def patch(self, request):
        profile = request.user.profile
        data = request.data

        if "diet" in data:
            if data["diet"] not in Profile.Diet.values:
                return Response(
                    {"error": "diet invalide"}, status=status.HTTP_400_BAD_REQUEST
                )
            profile.diet = data["diet"]

        if "allergies" in data:
            if not isinstance(data["allergies"], list):
                return Response(
                    {"error": "allergies doit etre une liste"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            profile.allergies = data["allergies"]

        if "skill_level" in data:
            if data["skill_level"] not in Profile.SkillLevel.values:
                return Response(
                    {"error": "skill_level invalide"}, status=status.HTTP_400_BAD_REQUEST
                )
            profile.skill_level = data["skill_level"]

        if "time_available_minutes" in data:
            try:
                minutes = int(data["time_available_minutes"])
                if minutes <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                return Response(
                    {"error": "time_available_minutes doit etre un entier positif"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            profile.time_available_minutes = minutes

        profile.save()
        return Response(serialize_profile(profile))
