import { themes, useThemeStore } from '../store/themeStore';
import { useTranslation } from '../store/languageStore';
import './ThemePicker.css';

interface ThemePickerProps {
  compact?: boolean;
  audience?: 'teacher' | 'student';
}

const ThemePicker: React.FC<ThemePickerProps> = ({ compact = false, audience = 'teacher' }) => {
  const { theme, setTheme } = useThemeStore();
  const { language, t } = useTranslation();
  const themeCopy: Record<string, [string, string]> = {
    midnight: ['Полуночная рабочая среда', 'Deep violet workspace'], studio: ['Тёплая бумага и терракота', 'Warm paper and terracotta'], terminal: ['Тёплый графит и киноварь', 'Warm graphite and vermilion'], aurora: ['Холодное стекло и циан', 'Cool glass and cyan'],
  };

  return (
    <section className={`theme-picker panel${compact ? ' theme-picker--compact' : ''}`}>
      <div className="theme-picker__intro">
        <span className="eyebrow">{t('Оформление', 'Appearance')}</span>
        <h3>{t('Тема интерфейса', 'Workspace theme')}</h3>
        <p>{audience === 'student' ? t('Выберите удобное оформление заданий и окна лайв-кодинга.', 'Choose a comfortable look for your tasks and live-coding workspace.') : t('Выберите оформление для всего приложения.', 'Preview a different visual direction across the entire application.')}</p>
      </div>
      <div className="theme-picker__options" role="radiogroup" aria-label={t('Тема интерфейса', 'Workspace theme')}>
        {themes.map((item) => <button key={item.id} type="button" role="radio" aria-checked={theme === item.id} className={theme === item.id ? 'theme-option theme-option--active' : 'theme-option'} onClick={() => setTheme(item.id)}>
          <span className="theme-option__swatch">{item.colors.map((color) => <i key={color} style={{ backgroundColor: color }} />)}</span>
          <span><b>{item.name}</b><small>{themeCopy[item.id][language === 'ru' ? 0 : 1]}</small></span>
          <em>{theme === item.id ? t('Выбрано', 'Selected') : t('Выбрать', 'Try')}</em>
        </button>)}
      </div>
    </section>
  );
};

export default ThemePicker;
