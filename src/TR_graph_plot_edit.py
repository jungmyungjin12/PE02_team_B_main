# 라이브러리 import
with open('library.txt','r') as f:
    for library in f:
        exec(library)
import functions as fc
import math
warnings.filterwarnings('ignore',category=np.RankWarning)
class plot_TR:
    def __init__(self,Lot,Wafer,Date,Position):
        self.Lot = Lot
        self.Wafer = Wafer
        self.Date = Date
        self.Position = Position
        self.label_font_properties = {'size':7,'weight':'bold'}
        self.title_font_properties = {'size':10,'weight':'bold'}
    def data_parse(self):
        self.wave_len = []
        self.wave_len_ref = np.array([])
        self.trans = []
        wave_len_half = []
        trans_half = []
        self.trans_ref = np.array([])
        wave_len_max = []
        trans_max = []
        self.bias = []
        self.I = []
        # smoothed_trans = np.array([])
        temp1 = 0
        temp2 = 0

        path = os.path.join('..', 'dat',self.Lot ,self.Wafer, self.Date)
        file_name = [os.path.join(path, f) for f in os.listdir(path) if
                     'LMZ' in f and f.endswith('.xml') and self.Position in f]

        tree = elemTree.parse(file_name[0])
        root = tree.getroot()

        for modulator in root.iter('Modulator'):
            for WL_sweep in modulator.iter('WavelengthSweep'):
                if temp1 == 1:
                    self.wave_len_ref = np.append(self.wave_len_ref, np.array(list(map(float, WL_sweep.find('L').text.split(',')))))
                    self.trans_ref = np.append(self.trans_ref, np.array(list(map(float, WL_sweep.find('IL').text.split(',')))))
                    continue
                self.wave_len.append(list(map(float, WL_sweep.find('L').text.split(','))))
                self.trans.append(list(map(float, WL_sweep.find('IL').text.split(','))))
                self.bias.append(float(WL_sweep.attrib['DCBias']))
                temp2 += 1
            temp1 += 1
        s = 150
        for i in range(len(self.wave_len)):
            fit_trans_ref = fc.Ref_fitted_func(self.wave_len_ref, self.trans_ref)(self.wave_len[i])
            self.trans[i] = [ x - y for x,y in zip(self.trans[i],fit_trans_ref)]
            # plt.plot(wave_len[i],trans[i])
            trans_half_temp = []
            wave_len_half_temp = []
            for k in range(len(self.wave_len[i])):
                count = 0
                if k >= (len(self.wave_len[i]) - (s + 1)):
                    continue
                for g in range(1, (s + 1)):
                    if self.trans[i][k] > self.trans[i][k + g]:
                        count += 1
                if count >= s - 3:
                    trans_half_temp.append(self.trans[i][k])
                    wave_len_half_temp.append(self.wave_len[i][k])
            wave_len_half.append(wave_len_half_temp)
            trans_half.append(trans_half_temp)
            # plt.plot(wave_len_half[i],trans_half[i],'ro',markersize=0.5)#######
        # plt.show()

        for i in range(len(wave_len_half)):
            wave_len_max_temp = []
            trans_max_temp = []
            for j in range(len(wave_len_half[i])):
                if j == 0:
                    wave_len_max_temp.append(wave_len_half[i][j])
                    trans_max_temp.append(trans_half[i][j])
                    continue
                elif j >= len(wave_len_half[i]) - 4:
                    continue
                if (wave_len_half[i][j + 2] - wave_len_half[i][j + 1]) >= (
                        wave_len_half[i][j + 1] - wave_len_half[i][j] + 4):
                    wave_len_max_temp.append(wave_len_half[i][j + 2])
                    trans_max_temp.append(trans_half[i][j + 2])

            if trans_max_temp[0] < trans_max_temp[1] + 0.5:
                wave_len_max.append(wave_len_max_temp[1:])
                trans_max.append(trans_max_temp[1:])
            else:
                wave_len_max.append(wave_len_max_temp)
                trans_max.append(trans_max_temp)

            # print(wave_len_max_temp,trans_max_temp)
            # plt.plot(wave_len_max[i],trans_max[i],'ro')
            # plt.plot(wave_len[i],fc.flat_fit_function(np.array(wave_len_max[i]), np.array(trans_max[i]))(wave_len[i]))
            self.trans[i] = [x-y for x,y in zip(self.trans[i],fc.flat_fit_function(np.array(wave_len_max[i]), np.array(trans_max[i]))(self.wave_len[i]))]  # flatten 한 데이터들로 다시 trans 변수를 할당
            # plt.plot(wave_len[i],trans[i],'b-')
            self.I.append([10 ** (x / 10) / 1000 for x in self.trans[i]])
        # print(I)
        # for i in range(temp2):
        #     plt.plot(wave_len[i],I[i])
        # 극댓값 정보를 찾기 -> 여러개 시도
        # print(I[bias.index(0.0)], wave_len[bias.index(0.0)])
        # print(bias)

        self.del_n_eff = []
        self.fitted_TR_data = []
        result_n_eff = fc.Transmission_fitting_n_eff(self.wave_len, self.I, self.bias)
        n_eff = result_n_eff[0]
        for bia in self.bias:
            if bia == 0.0:
                self.del_n_eff.append(0.0)
                self.fitted_TR_data.append(result_n_eff[1])
                continue
            result_del_n_eff = fc.Transmission_fitting_n_eff_V(self.wave_len, self.I, n_eff, self.bias, bia)
            self.del_n_eff.append(result_del_n_eff[0])
            self.fitted_TR_data.append(result_del_n_eff[1])
    def fitted_TR_graph_plot(self):
        for bia in self.bias:
            plt.plot(self.wave_len[self.bias.index(bia)],self.fitted_TR_data[self.bias.index(bia)],linewidth=0.8,label=f'{bia}V')
        plt.xlabel('wavelength[nm]',fontdict=self.label_font_properties)
        plt.ylabel('intensity[W]',fontdict=self.label_font_properties)
        plt.xticks(fontsize=6)  # modulate axis label's fontsize
        plt.yticks(fontsize=6)
        plt.title('Fitted Intensity Graph',fontdict=self.title_font_properties)
        plt.legend(loc='upper right',fontsize=5, ncol=2)
        plt.grid()
    def del_n_eff_by_voltage(self):
        plt.plot(self.bias, self.del_n_eff, 'r-')
        plt.axhline(0, color='black',linestyle='dashed',linewidth=1)  # x축에 대한 수평선
        plt.axvline(0, color='black',linestyle='dashed',linewidth=1)  # y축에 대한 수직선
        plt.xticks(fontsize=6)  # modulate axis label's fontsize
        plt.yticks(fontsize=6)
        plt.xlabel('voltage[V]', fontdict=self.label_font_properties)
        plt.ylabel(r'$\Delta$'+'n_eff', fontdict=self.label_font_properties)
        plt.title(r'$\Delta$'+'n_eff - Voltage Graph', fontdict=self.title_font_properties)
        plt.grid()

# 예시 사용 방법
test = plot_TR('HY202103','D08','20190712_113254','(-1,-1)')
test.data_parse()
# test.fitted_TR_graph_plot()
test.del_n_eff_by_voltage()
plt.show()