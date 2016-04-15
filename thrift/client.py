def connect_thrift():
    import sys
    sys.path.append('gen-py')

    from filesrv import Filesrv
    from filesrv.ttypes import Meta

    from thrift.transport import TSocket
    from thrift.transport import TTransport
    from thrift.protocol import TBinaryProtocol

    transport = TSocket.TSocket('192.168.2.20','9090')
    transport = TTransport.TBufferedTransport(transport)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = Filesrv.Client(protocol)

    transport.open()

@exec_time(time_limit=5)
def aws_upload(request):
    from PIL import Image
    import logging
    logger = logging.getLogger('aws_upload')
    results = []
    result = {}
    connect_thrift()

    for key in request.FILES.keys():
        file_obj = request.FILES[key]
        data = file_obj.read()
        fileid = hashlib.md5(data).hexdigest()
        result['size'] = file_obj.size
        result['name'] = file_obj.name
        c = request.POST.get('channel', None)
        if result['name'].lower().endswith('.apk'):
            apk_info = get_apk_info(file_obj)
            result['apk_info'] = apk_info
            result['apk_info']['md5'] = fileid
            if c is None:
                fileid = result['apk_info']['appid'] + '.apk'
            else:
                fileid = c + '/' + result['apk_info']['appid'] + '.apk'
            meta = Meta()
            meta.appid = apk_info['appid']
            meta.version_code = apk_info['version_code']
            meta.version_name = apk_info['version_name']
            meta.file_type = 'package'
            meta.ext = 'apk'
            client.save(data,meta)
        elif (request.META['HTTP_REFERER'].find('/wallpaper/') != -1 or 
                request.META['HTTP_REFERER'].find('/music/') != -1 ):
            client.save_media(data,'JPEG')
            if ((request.META['HTTP_REFERER'].find('/wallpaper/add') != -1
                    or request.META['HTTP_REFERER'].find('/wallpaper/edit') != -1)
                    and content_type.startswith('image') ):
                imgbuff = cStringIO.StringIO(data)
                img = Image.open(imgbuff)
                result['image_size'] = '{}x{}'.format(*img.size)
                nsize = (("medium", (800, 800)), ("small", (300, 300)))
                for n, size in nsize:
                    img_out = cStringIO.StringIO()
                    img.thumbnail(size, Image.ANTIALIAS)
                    img.save(img_out, "JPEG")
                    client.save_media(img_out.getvalue()),'JPEG')
        else:
            apk_info = request.POST.get('apk_info',None)#TODO:throw exception?
            result['apk_info'] = apk_info
            meta = Meta()
            meta.appid = apk_info['appid']
            meta.version_code = apk_info['version_code']
            meta.version_name = apk_info['version_name']
            meta.file_type = key
            meta.ext = 'png'
            client.save(data,meta)
        result['deleteUrl'] = '/file_delete'
        result['url'] =  fileid
        result['thumbnailUrl'] =  result['url']
        content_type = file_obj.content_type
        results.append(result)
        logger.info('{}  uploaded  {} successfully'.format(request.user, file_obj.name))
    return HttpResponse(json.dumps({'files':results}), content_type="application/json")

