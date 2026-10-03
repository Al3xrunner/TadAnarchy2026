export const CATEGORY = {
  heating: { pl: 'Brak ogrzewania / ciepłej wody', en: 'No heating / hot water', color: '#d1495b', phone: '993', phoneLabel: 'pogotowie ciepłownicze' },
  water: { pl: 'Brak wody', en: 'No water', color: '#2e86ab', phone: '994', phoneLabel: 'pogotowie wodociągowe' },
  power: { pl: 'Brak prądu', en: 'No power', color: '#e0a030', phone: '991', phoneLabel: 'pogotowie energetyczne' },
  flood: { pl: 'Podtopienie', en: 'Flooding', color: '#00798c', phone: '112', phoneLabel: 'numer alarmowy' },
  transit: { pl: 'Komunikacja', en: 'Transit problem', color: '#6a4c93' },
  danger: { pl: 'Zagrożenie', en: 'Danger', color: '#b3261e', phone: '112', phoneLabel: 'numer alarmowy' },
  other: { pl: 'Inne', en: 'Other', color: '#5c6b7a' },
}
export const LEVEL_COLOR = ['transparent', '#e0a030', '#d1495b']     // index = level 0 / 1 / 2
export const REPORTABLE = ['heating', 'water', 'power', 'flood', 'transit', 'danger']
