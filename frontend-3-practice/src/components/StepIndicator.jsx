// Индикатор шагов бронирования.
// Текущий шаг задаётся пропсом currentStep (1, 2 или 3).

const STEPS = [
  { id: 1, label: 'Услуга' },
  { id: 2, label: 'Дата и время' },
  { id: 3, label: 'Подтверждение' },
];

function StepIndicator({ currentStep }) {
  return (
    <ol className="steps">
      {STEPS.map((step) => {
        let className = 'steps__item';
        if (step.id < currentStep) className += ' steps__item--done';
        if (step.id === currentStep) className += ' steps__item--current';

        return (
          <li className={className} key={step.id}>
            <span className="steps__bullet">{step.id}</span>
            <span className="steps__label">{step.label}</span>
          </li>
        );
      })}
    </ol>
  );
}

export default StepIndicator;
