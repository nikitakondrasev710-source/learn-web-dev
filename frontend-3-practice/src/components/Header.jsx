function Header() {
  return (
    <header className="site-header">
      <a className="logo" href="#">
        <span className="logo__mark">Б</span>
        <span className="logo__text">
          <span className="logo__title">БРИТВА</span>
          <span className="logo__subtitle">барбершоп</span>
        </span>
      </a>

      <nav className="main-nav" aria-label="Основная навигация">
        <ul className="main-nav__list">
          <li className="main-nav__item">
            <a className="main-nav__link" href="#">
              Услуги
            </a>
          </li>
          <li className="main-nav__item">
            <a className="main-nav__link" href="#">
              Мастера
            </a>
          </li>
          <li className="main-nav__item">
            <a className="main-nav__link" href="#">
              Отзывы
            </a>
          </li>
          <li className="main-nav__item">
            <a className="main-nav__link" href="#">
              Контакты
            </a>
          </li>
        </ul>
      </nav>

      <div className="header-actions">
        <a className="header-actions__phone" href="tel:+74951234567">
          +7 (495) 123-45-67
        </a>
        <button className="button button--ghost" type="button">
          Войти
        </button>
      </div>
    </header>
  );
}

export default Header;
