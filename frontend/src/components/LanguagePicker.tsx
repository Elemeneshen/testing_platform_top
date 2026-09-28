import { useLanguageStore } from '../store/languageStore';

const LanguagePicker: React.FC = () => {
  const { language, setLanguage } = useLanguageStore();
  return <div className="language-picker" role="group" aria-label={language === 'ru' ? 'Выбор языка' : 'Language'}>
    <button type="button" className={language === 'ru' ? 'active' : ''} onClick={() => setLanguage('ru')} aria-pressed={language === 'ru'}>RU</button>
    <button type="button" className={language === 'en' ? 'active' : ''} onClick={() => setLanguage('en')} aria-pressed={language === 'en'}>EN</button>
  </div>;
};

export default LanguagePicker;
