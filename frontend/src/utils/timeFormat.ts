export const getUserTimeZone = (): string => {
  try {
    const timeZoneName = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const offsetMinutes = -new Date().getTimezoneOffset();
    const sign = offsetMinutes >= 0 ? '+' : '-';
    const hours = String(Math.floor(Math.abs(offsetMinutes) / 60)).padStart(2, '0');
    const mins = String(Math.abs(offsetMinutes) % 60).padStart(2, '0');
    return `${timeZoneName} (UTC${sign}${hours}:${mins})`;
  } catch {
    return 'Browser Local Time';
  }
};

export const convertLocalToIsoWithOffset = (localDateTimeString: string): string => {
  // datetime-local input provides naive YYYY-MM-DDTHH:mm; new Date parses as local time.
  const dateObj = new Date(localDateTimeString);
  if (isNaN(dateObj.getTime())) {
    throw new Error('Invalid date/time input');
  }
  return dateObj.toISOString();
};

export const formatEtaTimestamp = (isoTimestamp: string): string => {
  const dateObj = new Date(isoTimestamp);
  if (isNaN(dateObj.getTime())) {
    return isoTimestamp;
  }
  return dateObj.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short',
  });
};

export const formatDurationMinutes = (totalMinutes: number): string => {
  const hours = Math.floor(totalMinutes / 60);
  const minutes = Math.round(totalMinutes % 60);
  if (hours === 0) {
    return `${minutes} min`;
  }
  return `${hours}h ${minutes}m (${Math.round(totalMinutes)} min)`;
};
