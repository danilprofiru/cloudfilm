package src.main.com.cloudfilm;

import java.io.IOException;
import fi.iki.elonen.NanoHTTPD.*;

public class RTMPStreamServer extends NanoHTTPD {

    public RTMPStreamServer(int port) {
        super(port);
    }

    @Override    
    public Response serve(IHTTPSession session) {
        if (Method.GET.equals(session.getMethod())) {            
            
            // Получение значения параметра "filename" из запроса
            String filename = session.getParms().get("filename");
            
            if (filename != null && !filename.isEmpty()) {

                // Генерация ссылки на поток RTMP с использованием значения filename
                String rtmpUrl = generateRTMPUrl(filename);
                
                // Отправка ссылки в ответе на запрос                
                return newFixedLengthResponse("RTMP Stream URL: " + rtmpUrl);

            } else {                
                return newFixedLengthResponse("Parameter 'filename' is missing or empty");
            }        
        } else {
            return newFixedLengthResponse("Only GET requests are supported");        
        }
    }

    private String generateRTMPUrl(String filename) {        
        
        // Путь к файлу, который будет использоваться для создания RTMP-потока
        String filePath = "/home/danil/films/" + filename;

        // Команда для создания RTMP-потока с использованием ffmpeg        
        String ffmpegCommand = "ffmpeg -re -i " + filePath + " -c:v libx264 -preset ultrafast -c:a aac -f flv rtmp://192.168.1.14/myapp/" + filename;
        
        try {
            
            // Запуск процесса ffmpeg            
            ProcessBuilder processBuilder = new ProcessBuilder(ffmpegCommand.split(" "));
            processBuilder.start();
            
            // Вернуть URL вашего RTMP-потока            
            return "rtmp://95.165.93.233/myapp" + filename;
        } catch (IOException e) {            
            e.printStackTrace();
            return "Error generating RTMP URL";        }
    }

    public static void main(String[] args) {        
        int port = 8080; // Выбор порта для работы скрипта
        RTMPStreamServer server = new RTMPStreamServer(port);

        try {            
            server.start(NanoHTTPD.SOCKET_READ_TIMEOUT, false);
            System.out.println("RTMP Stream Server started on port " + port);        
        } catch (IOException e) {
            System.err.println("Error starting RTMP Stream Server: " + e.getMessage());        
        }
    }
}