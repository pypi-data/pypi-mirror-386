import cv2
import os
import glob
from animateplot.video.exceptions_animateplot import DirectoryNotExists

# Import compatível com diferentes versões do MoviePy
try:
    from moviepy import ImageClip, concatenate_videoclips
except ImportError:
    try:
        from moviepy.editor import ImageClip, concatenate_videoclips
    except ImportError:
        raise ImportError(
            "MoviePy não está instalado corretamente. "
            "Tente: pip uninstall moviepy && pip install moviepy==2.1.1"
        )


class RenderVideo:
    __dir_pattern_imgs = '.data'
    
    def __init__(self, list_images: list, fps: int = 15) -> None:
        """
        Inicializa o renderizador de vídeo
        
        Args:
            list_images: Lista de caminhos das imagens
            fps: Frames por segundo do vídeo final
        """
        if not list_images:
            raise ValueError("A lista de imagens não pode estar vazia")
        
        self.__images = list_images
        self.__fps = fps
        
        # Verifica se as imagens existem
        for img_path in self.__images:
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"Imagem não encontrada: {img_path}")
        
        # Ordena por data de modificação
        self.__images.sort(key=os.path.getmtime)
    
    def render_mp4(self, path_video: str, use_opencv: bool = False):
        """
        Renderiza o vídeo MP4
        
        Args:
            path_video: Caminho do arquivo de saída
            use_opencv: Se True, usa OpenCV (mais rápido); se False, usa MoviePy (melhor qualidade)
        """
        if use_opencv:
            self._render_with_opencv(path_video)
        else:
            self._render_with_moviepy(path_video)
    
    def _render_with_moviepy(self, path_video: str):
        """
        Renderiza usando MoviePy (melhor qualidade, mais lento)
        """
        print(f"Renderizando {len(self.__images)} frames com MoviePy...")
        
        time_frame = 1 / self.__fps
        
        # Cria clips das imagens
        clips = [ImageClip(img).set_duration(time_frame) for img in self.__images]
        
        # Concatena os clips
        concat_clip = concatenate_videoclips(clips, method="compose")
        
        # Escreve o vídeo com o FPS correto
        concat_clip.write_videofile(
            path_video, 
            fps=self.__fps,  # Usa o FPS definido no construtor
            codec='libx264',
            audio=False,
            logger='bar'  # Mostra barra de progresso
        )
        
        # Libera memória
        concat_clip.close()
        for clip in clips:
            clip.close()
        
        print(f"✓ Vídeo criado: {path_video}")
    
    def _render_with_opencv(self, path_video: str):
        """
        Renderiza usando OpenCV (mais rápido, boa qualidade)
        """
        print(f"Renderizando {len(self.__images)} frames com OpenCV...")
        
        # Lê a primeira imagem para pegar as dimensões
        first_img = cv2.imread(self.__images[0])
        if first_img is None:
            raise ValueError(f"Não foi possível ler a imagem: {self.__images[0]}")
        
        height, width, layers = first_img.shape
        
        # Define o codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # ou 'avc1' para H.264
        
        # Cria o VideoWriter
        video = cv2.VideoWriter(path_video, fourcc, self.__fps, (width, height))
        
        if not video.isOpened():
            raise RuntimeError("Não foi possível criar o arquivo de vídeo")
        
        # Adiciona cada frame
        for i, img_path in enumerate(self.__images):
            frame = cv2.imread(img_path)
            if frame is None:
                print(f"⚠ Aviso: Não foi possível ler {img_path}, pulando...")
                continue
            
            video.write(frame)
            
            # Progresso
            if (i + 1) % 10 == 0:
                print(f"Progresso: {i + 1}/{len(self.__images)} frames")
        
        video.release()
        print(f"✓ Vídeo criado: {path_video}")
    
    @classmethod
    def from_directory(cls, directory: str, pattern: str = '*.png', fps: int = 15):
        """
        Cria uma instância a partir de um diretório
        
        Args:
            directory: Caminho do diretório com as imagens
            pattern: Padrão de busca (*.png, *.jpg, etc)
            fps: Frames por segundo
        
        Returns:
            Instância de RenderVideo
        """
        if not os.path.isdir(directory):
            raise DirectoryNotExists(
                f'O caminho {directory} não existe ou não é um diretório',
                directory
            )
        
        images = glob.glob(os.path.join(directory, pattern))
        
        if not images:
            raise ValueError(f"Nenhuma imagem encontrada em {directory} com padrão {pattern}")
        
        return cls(images, fps)
    
    def get_images_count(self) -> int:
        """Retorna o número de imagens"""
        return len(self.__images)
    
    def get_video_duration(self) -> float:
        """Retorna a duração estimada do vídeo em segundos"""
        return len(self.__images) / self.__fps
    
    def preview_info(self):
        """Mostra informações sobre o vídeo a ser gerado"""
        print(f"Informações do Vídeo:")
        print(f"  - Número de frames: {self.get_images_count()}")
        print(f"  - FPS: {self.__fps}")
        print(f"  - Duração: {self.get_video_duration():.2f} segundos")
        
        # Pega dimensões da primeira imagem
        first_img = cv2.imread(self.__images[0])
        if first_img is not None:
            h, w, _ = first_img.shape
            print(f"  - Resolução: {w}x{h}")