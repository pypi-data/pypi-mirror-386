import matplotlib.pyplot as plt
import imageio
import os
import glob
import time
from statistics import median
import numpy as np

from animateplot.video.video_movie import RenderVideo as rv
from ipywidgets import Video


class AnimatePlot:
    """
    Classe para criar animações a partir de plots do Matplotlib
    Suporta exportação para GIF e MP4
    """
    
    pattern_savefig = '%(i)s_fig.png'
    pattern_dir = '/tmp/.animatplot_cache/'
    
    def __init__(self, space=None, callplot=None, plt=plt, args=None, dpi=None):
        """
        Inicializa o AnimatePlot
        
        Args:
            space: Lista ou array com os índices/valores para iteração
            callplot: Função que recebe (index, plt) e retorna o plot
            plt: Instância do matplotlib.pyplot
            args: Argumentos adicionais (deprecated)
            dpi: DPI para salvar as imagens
        """
        self.__pattern_dir_check()
        self.args = args
        self.images = []
        self.plt = plt
        self.dpi = dpi or 100  # DPI padrão
        
        # Validação e configuração
        if space is not None and callplot is not None:
            if not (isinstance(space, (list, np.ndarray))):
                raise TypeError("space deve ser uma lista ou numpy array")
            
            if not callable(callplot):
                raise TypeError("callplot deve ser uma função")
            
            self.plot = callplot
            self.x = space
            self.size = len(self.x)
        else:
            self.plot = None
            self.x = None
            self.size = 0
    
    def render_cache(self, show_progress=True, clear_previous=False):
        """
        Renderiza e salva todos os frames em cache
        
        Args:
            show_progress: Mostrar barra de progresso
            clear_previous: Limpar cache anterior antes de renderizar
        """
        if self.plot is None or self.x is None:
            raise ValueError("Plot e space devem ser definidos no construtor")
        
        # Limpa cache anterior se solicitado
        if clear_previous:
            self.delete_cache()
            self.__pattern_dir_check()
        
        # Verifica se já existe cache
        existing_images = sorted(
            glob.glob(os.path.join(self.pattern_dir, '*.png')),
            key=os.path.getmtime
        )
        
        if existing_images and not clear_previous:
            print(f'✓ Encontradas {len(existing_images)} imagens em cache!')
            self.images = existing_images
            return
        
        # Renderiza novos frames
        print(f'Renderizando {self.size} frames...')
        time_init = time.time()
        ping_list = []
        self.images = []
        
        for i in range(self.size):
            frame_start = time.time()
            
            # Gera o plot
            try:
                self.plot(i, self.plt)
            except Exception as e:
                print(f"\n✗ Erro ao gerar frame {i}: {e}")
                continue
            
            # Salva a imagem
            img_path = os.path.join(
                self.pattern_dir,
                self.pattern_savefig % {'i': str(i).zfill(5)}  # Zero-padding
            )
            
            try:
                # Garante que o diretório existe antes de salvar
                os.makedirs(self.pattern_dir, exist_ok=True)
                self.plt.savefig(img_path, dpi=self.dpi, bbox_inches='tight')
                self.plt.clf()  # Limpa a figura
                self.images.append(img_path)
            except Exception as e:
                print(f"\n✗ Erro ao salvar frame {i}: {e}")
                continue
            
            # Estatísticas de progresso
            frame_time = time.time() - frame_start
            ping_list.append(frame_time)
            
            if show_progress and i > 0:
                ping_median = median(ping_list)
                elapsed = time.time() - time_init
                remaining = ping_median * (self.size - i - 1)
                total_est = elapsed + remaining
                fps = 1 / ping_median if ping_median > 0 else 0
                
                progress = 100 * (i + 1) / self.size
                print(
                    f'Frame {i+1}/{self.size} '
                    f'[{progress:.1f}% | {fps:.1f} fps | '
                    f'⏱️ {elapsed:.1f}s | ⏳ {remaining:.1f}s | '
                    f'📊 {total_est:.1f}s total]',
                    end='\r',
                    flush=True
                )
        
        # Resumo final
        total_time = time.time() - time_init
        avg_fps = self.size / total_time if total_time > 0 else 0
        avg_ping = 1000 * total_time / self.size if self.size > 0 else 0
        
        print(f'\n✓ Renderização completa!')
        print(f'  {self.size} frames em {total_time:.1f}s')
        print(f'  Velocidade: {avg_fps:.1f} fps | Ping médio: {avg_ping:.1f}ms')
    
    def render_gif(self, path, fps=10, optimize=True):
        """
        Cria um GIF animado a partir dos frames
        
        Args:
            path: Caminho do arquivo GIF de saída
            fps: Frames por segundo
            optimize: Otimizar o GIF (reduz tamanho)
        """
        if not self.images:
            self._load_images_from_cache()
        
        if not self.images:
            raise ValueError("Nenhuma imagem disponível. Execute render_cache() primeiro.")
        
        print(f'Criando GIF com {len(self.images)} frames...')
        time_init = time.time()
        
        # Carrega as imagens
        imgs_data = []
        for i, img_path in enumerate(self.images):
            try:
                imgs_data.append(imageio.imread(img_path))
                if (i + 1) % 10 == 0:
                    print(f'Carregando imagens: {i+1}/{len(self.images)}', end='\r')
            except Exception as e:
                print(f"\n⚠ Aviso: Não foi possível ler {img_path}: {e}")
        
        # Salva o GIF
        duration = 1000 / fps  # duração em ms por frame
        imageio.mimsave(
            path,
            imgs_data,
            duration=duration,
            loop=0  # loop infinito
        )
        
        elapsed = time.time() - time_init
        file_size = os.path.getsize(path) / (1024 * 1024)  # MB
        
        print(f'\n✓ GIF salvo: {path}')
        print(f'  Tempo: {elapsed:.1f}s | Tamanho: {file_size:.2f} MB')
    
    def render_mp4(self, path_video, fps=15, use_opencv=True):
        """
        Cria um vídeo MP4 a partir dos frames
        
        Args:
            path_video: Caminho do arquivo MP4 de saída
            fps: Frames por segundo
            use_opencv: Usar OpenCV (rápido) ou MoviePy (alta qualidade)
        
        Returns:
            Widget de vídeo se estiver no Jupyter, senão None
        """
        if not self.images:
            self._load_images_from_cache()
        
        if not self.images:
            raise ValueError("Nenhuma imagem disponível. Execute render_cache() primeiro.")
        
        print(f'Criando vídeo MP4 com {len(self.images)} frames...')
        time_init = time.time()
        
        # Renderiza o vídeo
        render_video = rv(self.images, fps=fps)
        render_video.render_mp4(path_video, use_opencv=use_opencv)
        
        elapsed = time.time() - time_init
        file_size = os.path.getsize(path_video) / (1024 * 1024)  # MB
        
        print(f'✓ Vídeo salvo: {path_video}')
        print(f'  Tempo: {elapsed:.1f}s | Tamanho: {file_size:.2f} MB')
        
        # Retorna widget se estiver no Jupyter
        return self.play_jb_mp4(path_video)
    
    def play_jb_mp4(self, path):
        """
        Reproduz o vídeo no Jupyter Notebook
        
        Args:
            path: Caminho do arquivo de vídeo
        
        Returns:
            Widget de vídeo ou None
        """
        # Verifica se está rodando no Jupyter
        if 'JPY_PARENT_PID' in os.environ or self._is_notebook():
            if os.path.isfile(path):
                print(f"▶️  Reproduzindo: {path}")
                return Video.from_file(path, width=600, height=350)
        return None
    
    def _is_notebook(self):
        """Verifica se está rodando em um notebook"""
        try:
            from IPython import get_ipython
            if 'IPKernelApp' in get_ipython().config:
                return True
        except:
            pass
        return False
    
    def _load_images_from_cache(self):
        """Carrega imagens do cache se existirem"""
        if os.path.isdir(self.pattern_dir):
            self.images = sorted(
                glob.glob(os.path.join(self.pattern_dir, '*.png')),
                key=os.path.getmtime
            )
            if self.images:
                print(f'✓ {len(self.images)} imagens carregadas do cache')
    
    def delete_cache(self):
        """Remove todas as imagens do cache e o diretório"""
        if os.path.isdir(self.pattern_dir):
            file_imgs = glob.glob(os.path.join(self.pattern_dir, '*.png'))
            
            if file_imgs:
                print(f'Removendo {len(file_imgs)} imagens do cache...')
                for img in file_imgs:
                    try:
                        os.remove(img)
                    except Exception as e:
                        print(f"⚠ Aviso: Não foi possível remover {img}: {e}")
            
            try:
                os.rmdir(self.pattern_dir)
                print('✓ Cache limpo')
            except Exception as e:
                print(f"⚠ Aviso: Não foi possível remover diretório: {e}")
        
        self.images = []
    
    def get_cache_info(self):
        """Retorna informações sobre o cache"""
        if not os.path.isdir(self.pattern_dir):
            return {
                'exists': False,
                'count': 0,
                'size_mb': 0
            }
        
        images = glob.glob(os.path.join(self.pattern_dir, '*.png'))
        total_size = sum(os.path.getsize(img) for img in images)
        
        return {
            'exists': True,
            'count': len(images),
            'size_mb': total_size / (1024 * 1024),
            'path': os.path.abspath(self.pattern_dir)
        }
    
    def __pattern_dir_check(self):
        """Cria o diretório de cache se não existir"""
        if not os.path.isdir(self.pattern_dir):
            os.makedirs(self.pattern_dir, exist_ok=True)
    
    def __repr__(self):
        cache_info = self.get_cache_info()
        return (
            f"AnimatePlot("
            f"frames={self.size}, "
            f"cache={cache_info['count']} images, "
            f"size={cache_info['size_mb']:.2f}MB)"
        )