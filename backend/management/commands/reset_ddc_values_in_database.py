from django.core.management.base import BaseCommand, CommandError
import backend.models as models

class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        This function resets all DDC codes for resources. This is necessary whenever a new SidBERT model is uploaded.
        The function DOES NOT perform relabeling. This is taken care of in the scheduled tasks.
        """
        try:
            update_list = [
                models.InheritingCourse.objects.filter(ddc_code__isnull=False, title__isnull=False),
                models.InheritingEvent.objects.filter(ddc_code__isnull=False, title__isnull=False),]
            #    models.WebResource.objects.filter(ddc_code__isnull=False, title__isnull=False)
            #]
        except CommandError:
            raise CommandError('Could not access database for DDC data deletion!')
        if len(update_list) == 0:
            self.stdout.write('No Entries with DDC codes in Database!')
        else:
            self.stdout.write('Successfully aggregated objects for DDC code deletion. Deletion in progress...')
            try:
                for query_set in update_list:
                    for query_object in query_set:
                        query_object.ddc_code = None
                        query_object.save()
                self.stdout.write('Successfully deleted DDC codes from all backend resources :)')
            except CommandError:
                raise CommandError('Error deleting DDC codes.')


