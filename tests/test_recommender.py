from app.services.recommender import RecommendationService

def test_distance_zero():
    assert RecommendationService.distance_km(10, 20, 10, 20) == 0

def test_distance_is_symmetric():
    a = RecommendationService.distance_km(39.95, -75.16, 40.0, -75.2)
    b = RecommendationService.distance_km(40.0, -75.2, 39.95, -75.16)
    assert abs(a - b) < 1e-9
