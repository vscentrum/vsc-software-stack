import jcuda.runtime.JCuda;
import jcuda.runtime.cudaDeviceProp;
import jcuda.driver.JCudaDriver;

public class HelloJCuda {
  public static void main(String[] args) {
    JCuda.setExceptionsEnabled(true);
    int[] n = {0};
    JCuda.cudaGetDeviceCount(n);
    System.out.println("CUDA runtime sees devices: " + n[0]);
    for (int i=0; i<n[0]; i++) {
      cudaDeviceProp p = new cudaDeviceProp();
      JCuda.cudaGetDeviceProperties(p, i);
      String name = new String(p.name).trim();
      long memMiB = p.totalGlobalMem / (1024 * 1024);
      System.out.println("[" + i + "] " + name + " CC " + p.major + "." + p.minor + " Mem " + memMiB + " MiB");
    }
    JCudaDriver.setExceptionsEnabled(true);
    JCudaDriver.cuInit(0);
    int[] nd = {0};
    JCudaDriver.cuDeviceGetCount(nd);
    System.out.println("CUDA driver sees devices: " + nd[0]);
  }
}
