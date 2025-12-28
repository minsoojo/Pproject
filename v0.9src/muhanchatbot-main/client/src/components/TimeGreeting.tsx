import { useEffect, useState } from 'react';

// Add font styles
const fontStyles = `
  @font-face {
    font-family: 'PresentationLight';
    src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2404@1.0/Freesentation-3Light.woff2') format('woff2');
    font-weight: 300;
    font-display: swap;
  }
  @font-face {
    font-family: 'Presentation';
    src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2404@1.0/Freesentation-5Medium.woff2') format('woff2');
    font-weight: 500;
    font-display: swap;
  }
`;

// Add styles to document head
const styleElement = document.createElement('style');
styleElement.textContent = fontStyles;
document.head.appendChild(styleElement);

const TimeGreeting = () => {
  const [timeString, setTimeString] = useState<React.ReactNode>('');
  const [isWeekend, setIsWeekend] = useState(false);
  const [currentPeriod, setCurrentPeriod] = useState<{ period: number; isBreak: boolean } | null>(null);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const day = now.getDay(); // 0: 일요일, 1: 월요일, ..., 6: 토요일
      const hours = now.getHours();
      const minutes = now.getMinutes();
      const totalMinutes = hours * 60 + minutes;
      
      // 주말 확인 (0: 일요일, 6: 토요일)
      const weekend = day === 0 || day === 6;
      setIsWeekend(weekend);

      if (weekend) {
        setTimeString('좋은 주말 보내세요!');
        setCurrentPeriod(null);
        return;
      }

      // 교시 시간표 (시작 시간, 분, 교시 번호)
      const schedule = [
        { start: 9 * 60, period: 1 },   // 1교시: 09:00-09:50
        { start: 10 * 60, period: 2 },  // 2교시: 10:00-10:50
        { start: 11 * 60, period: 3 },  // 3교시: 11:00-11:50
        { start: 12 * 60, period: 4 },  // 4교시: 12:00-12:50
        { start: 13 * 60, period: 5 },  // 5교시: 13:00-13:50
        { start: 14 * 60, period: 6 },  // 6교시: 14:00-14:50
        { start: 15 * 60, period: 7 },  // 7교시: 15:00-15:50
        { start: 16 * 60, period: 8 },  // 8교시: 16:00-16:50
        { start: 17 * 60, period: 9 },  // 9교시: 17:00-17:50
        { start: 18 * 60, period: 10 }  // 10교시: 18:00-18:50
      ];

      // 현재 시간이 수업 시간인지 확인
      let currentPeriodInfo = null;
      let isBreakTime = false;

      for (let i = 0; i < schedule.length; i++) {
        const { start, period } = schedule[i];
        const end = start + 50; // 50분 수업

        if (totalMinutes >= start && totalMinutes < end) {
          currentPeriodInfo = { period, isBreak: false };
          break;
        } else if (i < schedule.length - 1 && totalMinutes >= end && totalMinutes < schedule[i + 1].start) {
          // 쉬는 시간 (10분)
          isBreakTime = true;
          currentPeriodInfo = { period: period + 1, isBreak: true };
          break;
        }
      }

      // 요일 한글 변환
      const days = ['일', '월', '화', '수', '목', '금', '토'];
      const dayName = days[day];
      
      // 수업 시간이 아닌 경우
      if (!currentPeriodInfo) {
        if (totalMinutes < 9 * 60 || totalMinutes >= 19 * 60) {
          setTimeString(
            <>
              <div>오늘은 {dayName}요일</div>
            </>
          );
          setCurrentPeriod(null);
          return;
        }
      }

      if (currentPeriodInfo) {
        const { period, isBreak } = currentPeriodInfo;
        if (isBreak) {
          setTimeString(
            <>
              <span>{dayName}요일 {period}교시 쉬는 시간</span>
            </>
          );
          setCurrentPeriod({ period, isBreak: true });
        } else {
          setTimeString(
            <>
              <span>{dayName}요일 {period}교시</span>
            </>
          );
          setCurrentPeriod({ period, isBreak: false });
        }
      } else {
        setTimeString(`오늘은 ${dayName}요일\n수업 시간이 아닙니다`);
        setCurrentPeriod(null);
      }
    };

    // 초기 실행
    updateTime();
    
    // 1분마다 업데이트
    const interval = setInterval(updateTime, 60000);
    
    // 컴포넌트 언마운트 시 인터벌 정리
    return () => clearInterval(interval);
  }, []);

  const renderClassInfo = () => {
    if (isWeekend) return null;
    
    if (currentPeriod) {
      if (currentPeriod.isBreak) {
        const now = new Date();
        const currentHour = now.getHours();
        const currentMinute = now.getMinutes();
        
        // Break time is always from :50 to :00 of the next hour
        const breakEndHour = currentMinute >= 50 ? currentHour + 1 : currentHour;
        const breakEndMinute = 0;
        
        // Calculate time remaining until next class (in minutes)
        const currentTime = now.getTime();
        const nextClassTime = new Date(now);
        if (currentMinute >= 50) {
          nextClassTime.setHours(currentHour + 1, 0, 0, 0);
        } else {
          nextClassTime.setHours(currentHour, 50, 0, 0);
        }
        const timeDiff = Math.max(0, Math.ceil((nextClassTime.getTime() - currentTime) / 60000)); // 분 단위로 변환
        
        return (
          <div className="mt-2 text-center">
            <div className="text-lg font-semibold text-green-600">
              쉬는 시간: {String(currentHour).padStart(2, '0')}:50~{String(breakEndHour).padStart(2, '0')}:00
            </div>
            <div className="text-sm text-gray-600">
              {timeDiff > 0 ? `다음 수업까지 ${timeDiff}분 남았어요` : '다음 수업이 곧 시작해요'}
            </div>
          </div>
        );
      } else {
        const periodInfo = [
          '1교시: 09:00 ~ 09:50 (50분)',
          '2교시: 10:00 ~ 10:50 (50분)',
          '3교시: 11:00 ~ 11:50 (50분)',
          '4교시: 12:00 ~ 12:50 (50분)',
          '5교시: 13:00 ~ 13:50 (50분)',
          '6교시: 14:00 ~ 14:50 (50분)',
          '7교시: 15:00 ~ 15:50 (50분)',
          '8교시: 16:00 ~ 16:50 (50분)',
          '9교시: 17:00 ~ 17:50 (50분)',
          '10교시: 18:00 ~ 18:50 (50분)'
        ][currentPeriod.period - 1];

        return (
          <div className="mt-2 text-center">
            <div className="text-lg font-semibold text-primary dark:text-white">
              {periodInfo}
            </div>
            <div className="text-sm text-gray-600">
              다음 쉬는 시간까지 {50 - (new Date().getMinutes() % 60)}분 남았어요
            </div>
          </div>
        );
      }
    }
    
    return (
      <div className="mt-2 text-center text-gray-700 text-lg">
        수업 시간이 아닙니다
      </div>
    );
  };

  return (
    <div className="w-full">
      <div className="text-2xl font-bold text-center text-primary dark:text-white mb-4 whitespace-nowrap">
        {timeString}
      </div>
      {renderClassInfo()}
    </div>
  );
};

export default TimeGreeting;