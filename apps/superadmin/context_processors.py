def superadmin(request):
    sa = getattr(request, 'superadmin', None)
    return {'superadmin_actual': sa}
