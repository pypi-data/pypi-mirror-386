import pydoc
import typing
from django.conf import settings
from django.http import JsonResponse
from rest_framework import generics, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework_tracking import mixins
from rest_framework import status

from karrio.core.utils import DP
from karrio.server.serializers import link_org
from karrio.server.tracing.utils import set_tracing_context
from karrio.server.core.utils import failsafe
from karrio.server.core.authentication import (
    TokenAuthentication,
    JWTAuthentication,
    TokenBasicAuthentication,
    OAuth2Authentication,
)
from karrio.server.core.models import APILogIndex

AccessMixin: typing.Any = pydoc.locate(
    getattr(settings, "ACCESS_METHOD", "karrio.server.core.authentication.AccessMixin")
)


class LoggingMixin(mixins.LoggingMixin):
    def handle_log(self):
        data = None if "data" not in self.log else DP.jsonify(self.log["data"])
        query_params = (
            None
            if "query_params" not in self.log
            else DP.jsonify(self.log["query_params"])
        )
        response = (
            dict(response=response)
            if "response" not in self.log
            else (
                DP.jsonify(self.log["response"])
                if isinstance(DP.to_object(self.log["response"]), dict)
                else self.log["response"]
            )
        )
        entity_id = failsafe(lambda: DP.to_dict(response)["id"])
        test_mode = failsafe(lambda: self.request.test_mode)

        if test_mode is None and '"test_mode": true' in (self.log["response"] or ""):
            test_mode = True
        if test_mode is None and '"test_mode": false' in (self.log["response"] or ""):
            test_mode = False

        log = APILogIndex(
            **{
                **self.log,
                "data": data,
                "response": response,
                "entity_id": entity_id,
                "test_mode": test_mode,
                "query_params": query_params,
            }
        )

        log.save()
        link_org(log, self.request)

        set_tracing_context(
            request_log_id=getattr(log, "id", None),
            object_id=failsafe(lambda: (self.log.get("response") or {}).get("id")),
        )


class BaseView:
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    authentication_classes = [
        TokenAuthentication,
        JWTAuthentication,
        OAuth2Authentication,
        TokenBasicAuthentication,
    ]


class BaseAPIView(views.APIView, BaseView):
    pass


class BaseGenericAPIView(generics.GenericAPIView, BaseView):
    def get_queryset(self):
        if hasattr(self, "model") and getattr(self, "swagger_fake_view", False):
            # queryset just for schema generation metadata
            return self.model.objects.none()

        if hasattr(self, "model") and hasattr(self.model, "access_by"):
            return self.model.access_by(self.request)

        return getattr(self, "queryset", None)


class GenericAPIView(LoggingMixin, BaseGenericAPIView):
    logging_methods = ["POST", "PUT", "PATCH", "DELETE"]


class APIView(LoggingMixin, BaseAPIView):
    logging_methods = ["POST", "PUT", "PATCH", "DELETE"]


class LoginRequiredView(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        auth = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return JsonResponse(
                dict(
                    errors=[
                        {
                            "code": "not_authenticated",
                            "message": "Authentication credentials were not provided.",
                        }
                    ]
                ),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not request.user.is_verified():
            return JsonResponse(
                dict(
                    errors=[
                        {"code": "not_verified", "message": "User is not verified."}
                    ]
                ),
                status=status.HTTP_403_FORBIDDEN,
            )
        return auth
