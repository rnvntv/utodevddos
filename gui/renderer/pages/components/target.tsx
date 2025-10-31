/** Компонент для отображения статуса целевого сайта. */

import Status, { statusLevelMap } from "./status";
import { TargetProps } from "../../types/props.d";


const Target = (props: TargetProps) => {
    return (
        <div className="targetContainer">
            <div className="target">
                <a href={props.url} className="targetUrl">
                    {
                        props.url ? (
                            <>
                                Атака на&nbsp;
                                <span>{props.url}</span>
                            </>
                        ) : (
                            'Ожидание цели...'
                        )
                    }
                </a>
                <div className="targetStatus">
                    Статус:&nbsp;
                    <div className="statusWrapper">
                        <Status
                            status={
                                // Удаляем префикс StatusCodes. из статуса.
                                (props.status || 'UNKNOWN')
                                .replace(/StatusCodes\./, '')
                                .replace(/_/, ' ')
                            }
                            level={statusLevelMap[props.status]}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Target;
