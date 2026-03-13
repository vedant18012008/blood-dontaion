from accounts.models import DonorBadge


def award_donor_badges(user):
    donation_count = user.donation_records.count()
    badges_to_award = []

    if donation_count >= 1:
        badges_to_award.append(DonorBadge.BadgeType.FIRST_DROP)
    if donation_count >= 5:
        badges_to_award.append(DonorBadge.BadgeType.FIVE_LIVES)
    if donation_count >= 10:
        badges_to_award.append(DonorBadge.BadgeType.LIFESAVER_HERO)

    for badge in badges_to_award:
        DonorBadge.objects.get_or_create(user=user, badge_type=badge)
