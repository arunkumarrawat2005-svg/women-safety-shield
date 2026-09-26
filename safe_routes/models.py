from django.db import models


class RouteSegment(models.Model):
    start_lat = models.FloatField()
    start_lng = models.FloatField()
    end_lat = models.FloatField()
    end_lng = models.FloatField()
    safety_score = models.FloatField(default=7.0, help_text="Predicted safety score (0.0 to 10.0)")
    last_scored_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_scored_at']

    def __str__(self):
        return f"Segment ({self.start_lat:.4f},{self.start_lng:.4f}) -> ({self.end_lat:.4f},{self.end_lng:.4f}): {self.safety_score}/10"
