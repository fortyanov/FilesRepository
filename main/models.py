from django.db.models import *
from django.contrib.auth.models import User


class File(Model):
    file = FileField(upload_to='')
    hash = CharField(max_length=1024)

    def __repr__(self):
        return '%s :: %s' % (self.file, self.hash)

class Repr(Model):
    reprname = CharField(max_length=1024)
    user = ForeignKey(User)
    file = ForeignKey(File)

    def __repr__(self):
        return '%s :: %s :: %s' % (self.reprname, self.user, self.file)


