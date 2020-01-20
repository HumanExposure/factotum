from factotum.environment import env


def settings(request):
    return {"enable_google_analytics": env.ENABLE_GOOGLE_ANALYTICS}
