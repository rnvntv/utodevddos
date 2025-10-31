/** Компонент для отображения ботнета */

import { useState, useEffect } from "react";

import Target from "./target";
import Bot from "./bot";

import { BotnetProps } from "../../types/props.d";
import { StatusCodes } from "../../types/enums.d";

const Botnet = () => {
    // Инициализация состояния ботнета.
    const [data, setData] = useState<BotnetProps>({
        target: {
            url: "",
            status: StatusCodes.NO_LUCK
        },
        botList: []
    });

    useEffect(() => {
        const updateBotnet = (botData: BotnetProps) => {
            // Присваиваем случайный аватар для каждого бота.
            botData.botList.forEach((bot, idx) => {
                bot.avatar = `/robots/${Math.round(idx % 9)}.png`;
            });
            setData(botData);
        }
        let source: EventSource;
        /* Если код запущен в Electron, мы можем получить доступ к Pipe Monitor
        через electronAPI мост. */
        if (window.electronAPI) {
            const piper = window.electronAPI.piper;
            const reload = window.electronAPI.reload;
            piper.monitor({
                onConnection: console.log,
                onError: console.error,
                onDisconnect: reload,
                // При получении сообщения, обновляем состояние ботнета.
                onData: updateBotnet
            });
        }
        // Иначе, получаем данные через HTTP Server-Sent Events (SSE) поток.
        else {
            // Используем HTTP API для работы в браузере.
            // Создаем EventSource для прослушивания HTTP потока.
            source = new EventSource("http://localhost:8888/api/stream");
            source.onmessage = (event) => {
                // При получении сообщения, обновляем состояние ботнета.
                const parsed: BotnetProps = JSON.parse(event.data);
                updateBotnet(parsed);
            }
        }
        return () => {
            if (source) {
                source.close();
                window.location.reload();
            }
        }
    }, []);

    return (
        <div className="botnet">
            <div className="target">
                <Target
                    url={data.target.url}
                    status={data.target.status}
                />
            </div>
            <div className="botlist">
                {data.botList.map(
                    (bot, index) => <Bot key={index} {...bot} />
                )}
            </div>
        </div>
    );
}

export default Botnet;
