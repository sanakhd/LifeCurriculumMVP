export const voiceMapping = {
  'Host A': 'Alloy',
  'Host B': 'Echo', 
  'narrator': 'Nova'
};

export const getDisplayName = (speaker: string): string => {
  return voiceMapping[speaker as keyof typeof voiceMapping] || speaker;
};
