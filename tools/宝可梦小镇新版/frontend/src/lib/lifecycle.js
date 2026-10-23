// The native domain uses Asia/Tokyo dates, independent of the host browser zone.
export function millisecondsUntilJapanMidnight(now = Date.now()) {
  const day = 86_400_000;
  return day - ((now + 9 * 3_600_000) % day) + 150;
}
